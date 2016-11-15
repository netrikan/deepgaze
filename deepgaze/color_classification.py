#!/usr/bin/env python

#The MIT License (MIT)
#Copyright (c) 2016 Massimiliano Patacchiola
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
#CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
#SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import numpy as np
import cv2
import sys

class HistogramColorClassifier:
    """Classifier for comparing an image I with a model M. The comparison is based on color
    histograms. It included an implementation of the Histogram Intersection algorithm.

    The histogram intersection was proposed by Michael Swain and Dana Ballard 
    in their paper "Indexing via color histograms".
    Abstract: The color spectrum of multicolored objects provides a a robust, 
    efficient cue for indexing into a large database of models. This paper shows 
    color histograms to be stable object representations over change in view, and 
    demonstrates they can differentiate among a large number of objects. It introduces 
    a technique called Histogram Intersection for matching model and image histograms 
    and a fast incremental version of Histogram Intersection that allows real-time 
    indexing into a large database of stored models using standard vision hardware. 
    Color can also be used to search for the location of an object. An algorithm 
    called Histogram Backprojection performs this task efficiently in crowded scenes.
    """

    def __init__(self, channels=[0, 1, 2], hist_size=[10, 10, 10], hist_range=[0, 256, 0, 256, 0, 256], hist_type='BGR'):
        """Init the classifier.

        This class has an internal list containing all the models.
        it is possible to append new models. Using the default values
        it extracts a 3D BGR color histogram from the image, using
	10 bins per channel.
        @param channels list where we specify the index of the channel 
           we want to compute a histogram for. For a grayscale image, 
           the list would be [0]. For all three (red, green, blue) channels, 
           the channels list would be [0, 1, 2].
        @param hist_size number of bins we want to use when computing a histogram. 
            It is a list (one value for each channel). Note: the bin sizes can 
            be different for each channel.
        @param hist_range it is the min-max value of the values stored in the histogram.
            For three channels can be [0, 256, 0, 256, 0, 256], if there is only one
            channel can be [0, 256]
        @param hsv_type Convert the input BGR frame in HSV or GRAYSCALE. before taking 
            the histogram. The HSV representation can get more reliable results in 
            situations where light have a strong influence.
            BGR: (default) do not convert the input frame
            HSV: convert in HSV represantation
            GRAY: convert in grayscale
        """
        self.channels = channels
        self.hist_size = hist_size
        self.hist_range = hist_range
        self.hist_type = hist_type
        self.model_list = list()

    def addModelHistogram(self, model_frame, index=-1):
        """Add the histogram to internal container.

        @param model_frame the frame to add to the model, its histogram
            is obtained and saved in internal list.
        @param index [not implemented]
        """
        if(self.hist_type=='HSV'): model_frame = cv2.cvtColor(model_frame, cv2.COLOR_BGR2HSV)
        elif(self.hist_type=='GRAY'): model_frame = cv2.cvtColor(model_frame, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([model_frame], self.channels, None, self.hist_size, self.hist_range)
        hist = cv2.normalize(hist).flatten()
        self.model_list.append(hist)

    def returnHistogramComparison(self, hist_1, hist_2, method='intersection'):
        """Return the comparison value of two histograms.

        Comparing an histogram with itself return 1.
        @param hist_1
        @param hist_2
        @param method the comparison method.
            intersection: (default) the histogram intersection (Swain, Ballard)
        """
        if(method=="intersection"):
            comparison = cv2.compareHist(hist_1, hist_2, cv2.cv.CV_COMP_INTERSECT)
        elif(method=="correlation"):
            comparison = cv2.compareHist(hist_1, hist_2, cv2.cv.CV_COMP_CORREL)
        else:
            raise ValueError('[DEEPGAZE] color_classification.py: the method specified ' + str(method) + ' is not supported.')
        return comparison

    def returnHistogramComparisonArray(self, image, method='intersection'):
        """Return the comparison array between all the model and the input image.

        The highest value represents the best match.
        @param image the image to compare
        @param method the comparison method.
            intersection: (default) the histogram intersection (Swain, Ballard)
        @return a numpy array containg the comparison value between each pair image-model
        """
        if(self.hist_type=='HSV'): image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        elif(self.hist_type=='GRAY'): image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        comparison_array = np.zeros(len(self.model_list))
        image_hist = cv2.calcHist([image], self.channels, None, self.hist_size, self.hist_range)
        image_hist = cv2.normalize(image_hist).flatten()
        counter = 0
        for model_hist in self.model_list:
            comparison_array[counter] = self.returnHistogramComparison(image_hist, model_hist, method=method)
            counter += 1
        return comparison_array

    def returnHistogramComparisonProbability(self, image, method='intersection'):
        """Return the probability distribution of the comparison between 
        all the model and the input image. The sum of the elements in the output
        array sum up to 1.

        The highest value represents the best match.
        @param image the image to compare
        @param method the comparison method.
            intersection: (default) the histogram intersection (Swain, Ballard)
        @return a numpy array containg the comparison value between each pair image-model
        """
        comparison_array = self.returnHistogramComparisonArray(image=image, method=method)
        comparison_distribution = np.divide(comparison_array, np.sum(comparison_array))
        return comparison_distribution

    def returnBestMatchIndex(self, image, method='intersection'):
        """Return the index of the best match value between the image and the internal models.

        @param image the image to compare
        @param method the comparison method.
            intersection: (default) the histogram intersection (Swain, Ballard)
        @return a numpy array containg the comparison value between each pair image-model
        """
        comparison_array = self.returnComparisonArray(image, method=method)
        return np.argmax(comparison_array)

