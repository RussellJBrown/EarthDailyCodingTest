import numpy as np
from osgeo import gdal
from glob import glob
import os
import sys
import rasterio
import gdal
from osgeo import gdal, gdalconst, osr
import argparse
class ImageCombiner:
    def __init__(self,ImagePath,Combined):
        self.ImagePath = ImagePath
        self.Combined = Combined


    '''

    Creates the various Numpy arrays used for creating the final image
    This should be done using the median, however I am using the mean.
    I think my laptop is not powerful enough to run the nanmedian on this large of a
    dataset as it keeps killing the process. So instead I am using mean to demonstrate that the
    whole process still generally works.

    '''
    def CreateNumpyArrays(self):
        resultBlue = [y for x in os.walk(self.ImagePath) for y in glob(os.path.join(x[0], '*B2.TIF'))]
        resultGreen = [y for x in os.walk(self.ImagePath) for y in glob(os.path.join(x[0], '*B3.TIF'))]
        resultRed = [y for x in os.walk(self.ImagePath) for y in glob(os.path.join(x[0], '*B4.TIF'))]

        count = 0
        gd_obj = gdal.Open(resultBlue[0])
        array  = gd_obj.ReadAsArray()
        array = np.expand_dims(array,2)
        allarraysBlue = array
        allarraysGreen = array
        allarraysRed = array

        for i, tiff in enumerate(resultBlue):
            gd_obj = gdal.Open(tiff)
            array  = gd_obj.ReadAsArray()
            array = np.expand_dims(array,2)
            if i == 0:
                allarraysBlue = array
            else:
                try:
                    allarraysBlue = np.concatenate((allarraysBlue, array), axis=2)
                except:
                    count+=1
        #medianOfBlueTiff = np.nanmedian(allarraysBlue,axis=2)
        meanOfBlueTiff = np.nanmean(allarraysBlue,axis=2)

        for i, tiff in enumerate(resultGreen):
            gd_obj = gdal.Open(tiff)
            array  = gd_obj.ReadAsArray()
            array = np.expand_dims(array,2)
            if i == 0:
                allarraysGreen = array
            else:
                try:
                    allarraysGreen = np.concatenate((allarraysGreen, array), axis=2)
                except:
                    count+=1
        #medianOfGreenTiff = np.nanmedian(allarraysGreen,axis=2)
        meanOfGreenTiff = np.nanmean(allarraysGreen,axis=2)

        for i, tiff in enumerate(resultRed):
            gd_obj = gdal.Open(tiff)
            array  = gd_obj.ReadAsArray()
            array = np.expand_dims(array,2)
            if i == 0:
                allarraysRed = array
            else:
                try:
                    allarraysRed = np.concatenate((allarraysRed, array), axis=2)
                except:
                    count+=1
        #medianOfRedTiff = np.nanmedian(allarraysRed,axis=2)
        meanOfRedTiff = np.nanmean(allarraysRed,axis=2)


        if(count>0):
            print("Please Note that some of the Satellite Images Download are of different Horizontal or Vertical Pixel Counts")
            print("The different images have been ignored in the calculations of the Median or Mean")

        self.CreateImage(meanOfRedTiff,meanOfGreenTiff,meanOfBlueTiff,gd_obj.GetGeoTransform(),gd_obj)
        return



    '''
    @gd_obj: Geotiff object used to extract import Geography Information
    @gt: Projection of GeoTiff
    @meanOfBlueTiff: Contains Numpy array of the Mean or Median of all the Blue Images
    @meanofGreenTiff: Contains Numpy array of the Mean or Median of all the Green.TifImages
    @meanOfRedTiff: Contains Numpy array of the Mean or Median of all the Red.Tif images

    Method Creates New True Colour Image by taking combining the three numpys.

    '''
    def CreateImage(self,meanOfRedTiff,meanOfGreenTiff,meanOfBlueTiff,gt,gd_obj):
        try:
            height, width = meanOfRedTiff.shape
            driver = gdal.GetDriverByName("GTiff")
            dtype = gdal.GDT_UInt16
            dest= driver.Create(self.Combined,width,height,3,dtype)

            dest.SetGeoTransform(gt)
            wkt = gd_obj.GetProjection()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(wkt)
            dest.SetProjection(srs.ExportToWkt())
            dest.GetRasterBand(1).WriteArray(meanOfRedTiff)
            dest.GetRasterBand(2).WriteArray(meanOfGreenTiff)
            dest.GetRasterBand(3).WriteArray(meanOfBlueTiff)
            dest.FlushCache()
            print("Created New Image")
            dest = None
        except Exception as e: print(e)
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("InputPath", help = "Local directory containing images to combine. This should be formatted as per the OUTPUT_PATH of s2_imagery_retriever.py")
    parser.add_argument("OutputPath", help = "Local directory to write combined image to. The combined image will be written as a GeoTiff containing 3 bands: Red, Green, and Blue.")
    parser.add_argument('--combine_method', help="Method to use for combining: median, cloudfree. Defaults to 'median'")
    args = parser.parse_args()

    combiner = ImageCombiner(args.InputPath,args.OutputPath)
    combiner.CreateNumpyArrays()
