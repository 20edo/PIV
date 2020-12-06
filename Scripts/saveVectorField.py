#!/usr/bin/env python
# coding: utf-8

def saveVectorField(image_number):
        print('Processing image number:'+ image_number)
        # Camera
        resolution = (992,1004) #pixel
        physical_window = (45,45) # m
        pixel_depth = 8 # bit
        dynamic_range = 2**pixel_depth # levels
        scaling_factor = 1/(np.mean(physical_window)/np.mean(resolution)) # m/pixel

        frame_a  = tools.imread( folder + '/Images/A' + image_number + 'a.tif' )
        frame_b  = tools.imread( folder + '/Images/A' + image_number + 'b.tif' )



    # Image equalization
        def image_equalization(frame,dynamic_range,plot=0):
            frame = np.array(frame)
            # Histogram and cdf of the original image
            hist,bins = np.histogram(frame.flatten(),dynamic_range,[0,dynamic_range])
            cdf = hist.cumsum()
            cdf_normalized = cdf * hist.max()/ cdf.max()
            
            #Image equalization
            cdf_m = np.ma.masked_equal(cdf,0)
            cdf_m = (cdf_m - cdf_m.min())*255/(cdf_m.max()-cdf_m.min())
            cdf = np.ma.filled(cdf_m,0).astype('uint8')
            frameEQ = cdf[frame]    
            
            # Histogram and cdf of the equalized image
            frameEQ = np.array(frameEQ)
            histEQ,binsEQ = np.histogram(frameEQ.flatten(),dynamic_range,[0,dynamic_range])
            cdfEQ = histEQ.cumsum()
            cdf_normalizedEQ = cdfEQ * histEQ.max()/ cdfEQ.max()
            
            # Plot
            if plot:
                # Oriinal image
                ax1 = plt.subplot(1,2,1)
                ax1.plot(cdf_normalized, color = 'b')
                ax1.hist(frame.flatten(),dynamic_range,[0,dynamic_range], color = 'r')
                ax1.set_xlim([0,dynamic_range])
                ax1.legend(('cdf','histogram'), loc = 'upper left')
                ax1.set_title('Original image')
                # Equalized image
                ax2 = plt.subplot(1,2,2)
                ax2.plot(cdf_normalizedEQ, color = 'b')
                ax2.hist(frameEQ.flatten(),dynamic_range,[0,dynamic_range], color = 'r')
                ax2.set_xlim([0,dynamic_range])
                ax2.legend(('cdf','histogram'), loc = 'upper left')
                ax2.set_title('Equalized image')
                plt.show()
                
            return frameEQ


        frame_a = image_equalization(frame_a,dynamic_range,plot=0)


        frame_b = image_equalization(frame_b,dynamic_range,plot=0)

        winsize = 32 # pixels, interrogation window size in frame A
        searchsize = 38  # pixels, search in image B
        overlap = 30 # pixels, 50% overlap
        dt = 1/15 # sec, time interval between pulses


        u0, v0, sig2noise = pyprocess.extended_search_area_piv(frame_a.astype(np.int32), 
                                                               frame_b.astype(np.int32), 
                                                               window_size=winsize, 
                                                               overlap=overlap, 
                                                               dt=dt, 
                                                               search_area_size=searchsize, 
                                                               sig2noise_method='peak2peak')

        x, y = pyprocess.get_coordinates( image_size=frame_a.shape, 
                                         search_area_size=searchsize, 
                                         overlap=overlap )

        u1, v1, mask = validation.sig2noise_val( u0, v0, 
                                                sig2noise, 
                                                threshold = 1.05 )

        # filter out outliers that are very different from the
        # neighbours

        u2, v2 = filters.replace_outliers( u1, v1, 
                                          method='localmean', 
                                          max_iter=3, 
                                          kernel_size=3)

        # convert x,y to mm 
        # convert u,v to mm/sec

        x, y, u3, v3 = scaling.uniform(x, y, u2, v2, 
                                       scaling_factor = scaling_factor )
        # Copy the values of u and v (not sure it's useful) to output them
        uOut,vOut = np.copy(u3),np.copy(v3)

        #save in the simple ASCII table format
        tools.save(x, y, u3, v3, sig2noise, mask, folder + '/Vector_field/exp1_' + image_number + '.txt' )

        return uOut,vOut
