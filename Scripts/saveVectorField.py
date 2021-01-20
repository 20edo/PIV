#!/usr/bin/env python
# coding: utf-8

def checkerboard(shape):
    return np.indices(shape).sum(axis=0) % 2

def saveVectorField(image_number, save=0, minus_average=0, fill='checkerboard'):
        'Saves the vector field associated to the given image number, Requires flas_mask function'
        import skimage 
        import skimage.exposure as exposure
        import skimage.morphology as morphology
        from skimage.filters import rank
        import warnings

        # Print infos about the number the program is writing
        print('Processing image number:'+ image_number)
        # Camera
        resolution = (992,1004) #pixel
        physical_window = (45,45) # m
        pixel_depth = 8 # bit
        dynamic_range = 2**pixel_depth # levels
        scaling_factor = 1/(np.mean(physical_window)/np.mean(resolution)) # m/pixel
        # Read frames data
        if minus_average:
            frame_a  = tools.imread( folder + '/Images/ImagesMinusAverage/A' + image_number + 'a.tif' )
            frame_b  = tools.imread( folder + '/Images/ImagesMinusAverage/A' + image_number + 'b.tif' )
        else:
            frame_a  = tools.imread( folder + '/Images/A' + image_number + 'a.tif' )
            frame_b  = tools.imread( folder + '/Images/A' + image_number + 'b.tif' )

        if True:
            # Save masked and flashed regions
            flashMask_a, number_a = flash_mask(frame_a)
            flashMask_b, number_b = flash_mask(frame_b)

            if fill == 'noise' :
                # Replace flashed regions with a random noise
                    seed_a = int(image_number) + ord('a')
                    generator = np.random.default_rng(seed_a) # Seed a generator for results to be reproducigles
                    noise = generator.uniform(0,256, np.shape(flashMask_a))
                    # noise = noise*flashMask_a
                    noise = noise.astype(int)
                    noise = skimage.util.img_as_ubyte(noise.astype('uint8'))
                    frame_a = noise*flashMask_a+frame_a*(1-flashMask_a)

                    seed_b = int(image_number) + ord('b')
                    generator = np.random.default_rng(seed_b) # Seed a generator for results to be reproducibles
                    noise = generator.uniform(0,256, np.shape(flashMask_b))
                    noise = noise.astype(int)
                    noise = skimage.util.img_as_ubyte(noise.astype('uint8'))
                    frame_b = noise*flashMask_b+frame_b*(1-flashMask_b)

            elif fill == 'checkerboard':
                # Replace flash with checkerboard
                    check = 255*checkerboard(np.shape(flashMask_a))
                    check = check * flashMask_a
                    check = check.astype(int)
                    frame_a = check*flashMask_a+frame_a*(1-flashMask_a)


                    # Replace flash with checkerboard
                    check = 255*checkerboard(np.shape(flashMask_b))
                    check = check * flashMask_b
                    check = check.astype(int)
                    frame_b = check*flashMask_b+frame_b*(1-flashMask_b)

            else:
                error('fill not correct. Use checkerboard or noise')

            # Warn the user if some flashed region has been identified
            if number_a > 0:
                warnings.warn(str(number_a)+ ' flashed regions in frame a have been replaced with a random noise')

            if number_b > 0:
                warnings.warn(str(number_a)+ ' flashed regions in frame a have been replaced with a random noise')


           # Convert for rank filter
           # frame_a = skimage.util.img_as_ubyte(frame_a)
           # frame_b = skimage.util.img_as_ubyte(frame_a)

        # Equalize images

        selem = morphology.disk(70)     # Element that defines the pixels to be considered for the equalization

        frame_a = frame_a.astype('uint8')
        frame_a = rank.equalize(frame_a, selem = selem)

        frame_b = frame_b.astype('uint8')
        frame_b = rank.equalize(frame_b, selem = selem)

        if minus_average:
            location = '/Images/ImagesCorrectedMinusAverage/A'
        else:
            location = '/Images/ImagesCorrected/A'
        if save:
            plt.imsave(folder + location + str(image_number) + 'a.tif',frame_a, format='tiff',cmap=plt.cm.gray, vmin=0, vmax=255)
            plt.imsave(folder + location + str(image_number) + 'b.tif',frame_b, format='tiff',cmap=plt.cm.gray, vmin=0, vmax=255)
            np.save(folder+ location + str(image_number) + 'a', frame_a)
            np.save(folder+ location + str(image_number) + 'b', frame_b)

        # PIV cross correlation algorithm
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
        # Find the coordinates associated at each vector
        x, y = pyprocess.get_coordinates( image_size=frame_a.shape, 
                search_area_size=searchsize, 
                overlap=overlap )
        # Save into a mask the vectors with a low sing2noise ratio
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
        name = folder + '/Vector_field/exp1_' + image_number + '.txt'
        tools.save(x, y, u3, v3, mask, filename = name )

        return x,y,uOut,vOut,sig2noise, mask
