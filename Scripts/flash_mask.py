def flash_mask(image, bin_treshold=250, region_connectivity=1, area_treshold=100):
    '''Returns a mask with true where the image is flashed
    *****************************INPUTS
    bin_treshold        -> Threshold for binarization
    region_connectivity -> Value of connectivity used to look for regions (1    or 2)
    area_trshold        -> Minimum area required to consider a region flashed
    *****************************OUTPUTS
    mask                -> 1 where the image is flashed
    number              -> Number of flashed regions'''
    import numpy as np
    from skimage import morphology
    import skimage.measure as measure
    import skimage.segmentation as segmentation
    import skimage as sk
    import pandas as pd
    
    # Image binarization
    binarization = image > bin_treshold
    binarization = binarization.astype('uint8')

    # Calculate otsu treshold
    tresh = sk.filters.threshold_otsu(image)

    # Morphological closing ( holes inside a flashed region mean nothing)
    selem = sk.morphology.square(2)	# Not used
    bw = sk.morphology.closing(image > tresh)	# Uses a cross of dimension 2, connectivity = 1
    
    # Split the image in regions
    labeled_image = sk.measure.label(bw,connectivity=region_connectivity)
    
    # Inizialize mask 
    mask = np.zeros_like(image)
    number = 0
    # Turn to 1 positions where image is flashed
    for region in sk.measure.regionprops(labeled_image):
        if region.area >= area_treshold:
            min_row, min_col, max_row, max_col = region.bbox
            mask[min_row:max_row,min_col:max_col] = region.filled_image
            number +=1
    
    return mask, number
