
import os
import datetime
import matplotlib.pyplot as plt
import sys
import statistics
import argparse
import subprocess
import boto3
import wget
import pandas as pd
import geopandas as gpd
from botocore.handlers import disable_signing
from datetime import datetime as dt

import io
import ogr
import shapely.wkt
import shapely.geometry
import urllib.request
import zipfile
from pathlib import Path


s3 = boto3.resource('s3')
s3.meta.client.meta.events.register('choose-signer.s3.*',disable_signing)
bucket = 'landsat-pds'
my_bucket = s3.Bucket(bucket)



class ImageryAnalysis:
    def __init__(self,Path,Row,StartTime,FinishTime,DownloadPath):
        self.Path = Path
        self.Row = Row
        self.StartTime = StartTime
        self.FinishTime = FinishTime
        self.DownloadPath = DownloadPath



    '''
    Downloads the Data to the appropriate Folder
    '''
    def getLandsatData(self):
        print("Downloading Landsat Data")
        prefix="c1/L8/{}/{}/".format(self.Path,self.Row)
        for file in my_bucket.objects.filter(Prefix=prefix):
            vsis_image_path = os.path.join("/vsis3/",bucket,file.key).replace("\\","/")
            getYear = vsis_image_path.split("_")
            imageYear = getYear[3]
            ImageAquired = dt.strptime(imageYear,"%Y%m%d")
            MinYearCanBe = dt.strptime(self.StartTime,"%Y-%m-%d")
            MaxYearCanBe = dt.strptime(self.FinishTime,"%Y-%m-%d")

            getDownloadableImageLocation=vsis_image_path.split("/")
            if (vsis_image_path.endswith("B4.TIF") or vsis_image_path.endswith("B3.TIF") or vsis_image_path.endswith("B2.TIF")) and ImageAquired>MinYearCanBe and MaxYearCanBe>ImageAquired:
                print("Downloading: " + vsis_image_path)
                my_bucket.download_file(file.key,self.DownloadPath+getDownloadableImageLocation[8])
        print("Finished Downloading Data")
        return



    '''
    Method Not Currently Being Used
    The code can be changed so that the user inputs a bounding box instead of Path and Row.
    This method will than convert the bounding box to Path and Row

    '''
    def convertLatLongToRowPath(self):
        url = "https://prd-wret.s3-us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/atoms/files/WRS2_descending_0.zip"
        r = urllib.request.urlopen(url)
        print("Downloading shapefile to find Path and Row")
        zip_file = zipfile.ZipFile(io.BytesIO(r.read()))
        zip_file.extractall("landsat-path-row")
        zip_file.close()
        shapefile = 'landsat-path-row/WRS2_descending.shp'
        wrs = ogr.Open(shapefile)
        layer = wrs.GetLayer(0)
        pointLeft = shapely.geometry.Point(self.UpperLeftLong,self.UpperLeftLat)
        pointRight = shapely.geometry.Point(self.LowerRightLong,self.LowerRightLat)
        mode = 'D'

        i=0
        while not self.checkPoint(layer.GetFeature(i),pointLeft,mode):
            i+=1
        feature=layer.GetFeature(i)
        pathLeft = feature['PATH']
        rowLeft = feature['ROW']

        i=0
        while not self.checkPoint(layer.GetFeature(i),pointRight,mode):
            i+=1
        feature = layer.GetFeature(i)
        pathRight = feature['PATH']
        rowRight = feature['ROW']

        path = pathLeft
        row = rowLeft
        if pathLeft != pathRight or rowLeft!=rowRight:
            print("The extents selected span multiple paths and or rows. This program only works with 1 path or row")
            print("First Path and Row Type 1: " + " Path: " + str(pathLeft) +" Row: "+ str(rowLeft))
            print("First Path and Row Type 2: " + " Path: " + str(pathRight) +" Row: "+ str(rowRight))
            while True:
                answer = input("Type Answer: ")
                if(answer==str(1)):
                    break
                elif(answer==str(2)):
                    path,row = pathRight,rowRight
                    break
        return path,row




    '''
    Method Not Currently Being used
    If the user wants to use a bounding box instead this a helper Method
    to check if the point is in a certain Path and Row.

    @mode:
    @point: Point of Interest
    @feature: Feature of Interest from Shapefile previous downloaded
    '''
    def checkPoint(self,feature, point, mode):
        geom = feature.GetGeometryRef() #Get geometry from feature
        shape = shapely.wkt.loads(geom.ExportToWkt()) #Import geometry into shapely to easily work with our point
        if point.within(shape) and feature['MODE']==mode:
            return True
        else:
            return False





if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "Retrieve Landsat8 imagery tiles over area and time range of interest")

    parser.add_argument("Path",help="Path of Landsat8 Satellite")
    parser.add_argument("Row",help="Row of Landsat8 Satellite")
    parser.add_argument("StartDate",help="Start Date")
    parser.add_argument("EndDate",help="End Date")
    parser.add_argument("OutputPath",help="Output Path")


    args = parser.parse_args()

    Path(args.OutputPath).mkdir(parents=True, exist_ok=True)
    image=ImageryAnalysis(args.Path,args.Row,args.StartDate, args.EndDate,args.OutputPath)
    image.Path=str(image.Path)
    image.Row=str(image.Row)
    image.Path = image.Path.zfill(3)
    image.Row = image.Row.zfill(3)
    image.getLandsatData()
