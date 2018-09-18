__author__ = 'JeffreyTang'

try:
    from skimage import color, transform, restoration, io, feature
    import cv2
except ImportError:
    print 'CV2 not installed, cannot use sift_crop()...'

import matplotlib.pyplot as plt
import numpy as np
import os
import itertools
from scipy.spatial.distance import euclidean
from collections import defaultdict


class ImagePipeline(object):

    def __init__(self, parent_dir):
        """
        Manages reading, transforming and saving images

        :param parent_dir: Name of the parent directory containing all the sub directories
        """
        # Define the parent directory
        self.parent_dir = parent_dir

        # Sub directory variables that are filled in when read()
        self.raw_sub_dir_names = None
        self.sub_dirs = None
        self.label_map = None

        # Image variables that are filled in when read() and vectorize()
        self.img_lst2 = []
        self.img_names2 = []
        self.features = None
        self.labels = None

    def _make_label_map(self):
        """
        Get the sub directory names and map them to numeric values (labels)

        :return: A dictionary of dir names to numeric values
        """
        return {label: i for i, label in enumerate(self.raw_sub_dir_names)}

    def _path_relative_to_parent(self, some_dir):
        """
        Get the full path of a sub directory relative to the parent

        :param some_dir: The name of a sub directory
        :return: Return the full path relative to the parent
        """
        cur_path = os.getcwd()
        return os.path.join(cur_path, self.parent_dir, some_dir)

    def _make_new_dir(self, new_dir):
        """
        Make a new sub directory with fully defined path relative to the parent directory

        :param new_dir: The name of a new sub dir
        """
        # Make a new directory for the new transformed images
        new_dir = self._path_relative_to_parent(new_dir)
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)
        else:
            raise Exception('Directory already exist, please check...')

    def _empty_variables(self):
        """
        Reset all the image related instance variables
        """
        self.img_lst2 = []
        self.img_names2 = []
        self.features = None
        self.labels = None

    @staticmethod
    def _accpeted_file_format(fname):
        """
        Return boolean of whether the file is of the accepted file format

        :param fname: Name of the file in question
        :return: True or False (if the file is accpeted or not)
        """
        formats = ['.png', '.jpg', '.jpeg', '.tiff']
        for fmt in formats:
            if fname.endswith(fmt):
                return True
        return False

    @staticmethod
    def _accepted_dir_name(dir_name):
        """
        Return boolean of whether the directory is of the accepted name (i.e. no hidden files)

        :param dir_name: Name of the directory in question
        :return: True or False (if the directory is hidden or not)
        """
        if dir_name.startswith('.'):
            return False
        else:
            return True

    def _assign_sub_dirs(self, sub_dirs=tuple('all')):
        """
        Assign the names (self.raw_sub_dir_names) and paths (self.sub_dirs) based on
        the sub dirs that are passed in, otherwise will just take everything in the
        parent dir

        :param sub_dirs: Tuple contain all the sub dir names, else default to all sub dirs
        """
        # Get the list of raw sub dir names
        if sub_dirs[0] == 'all':
            self.raw_sub_dir_names = os.listdir(self.parent_dir)
        else:
            self.raw_sub_dir_names = sub_dirs
        # Make label to map raw sub dir names to numeric values
        self.label_map = self._make_label_map()

        # Get the full path of the raw sub dirs
        filtered_sub_dir = filter(self._accepted_dir_name, self.raw_sub_dir_names)
        self.sub_dirs = map(self._path_relative_to_parent, filtered_sub_dir)

    def read(self, sub_dirs=tuple('all')):
        """
        Read images from each sub directories into a list of matrix (self.img_lst2)

        :param sub_dirs: Tuple contain all the sub dir names, else default to all sub dirs
        """
        # Empty the variables containing the image arrays and image names, features and labels
        self._empty_variables()

        # Assign the sub dir names based on what is passed in
        self._assign_sub_dirs(sub_dirs=sub_dirs)

        for sub_dir in self.sub_dirs:
            img_names = filter(self._accpeted_file_format, os.listdir(sub_dir))
            self.img_names2.append(img_names)

            img_lst = [io.imread(os.path.join(sub_dir, fname)) for fname in img_names]
            self.img_lst2.append(img_lst)

    def save(self, keyword):
        """
        Save the current images into new sub directories

        :param keyword: The string to append to the end of the original names for the
                        new sub directories that we are saving to
        """
        # Use the keyword to make the new names of the sub dirs
        new_sub_dirs = ['%s.%s' % (sub_dir, keyword) for sub_dir in self.sub_dirs]

        # Loop through the sub dirs and loop through images to save images to the respective subdir
        for new_sub_dir, img_names, img_lst in zip(new_sub_dirs, self.img_names2, self.img_lst2):
            new_sub_dir_path = self._path_relative_to_parent(new_sub_dir)
            self._make_new_dir(new_sub_dir_path)

            for fname, img_arr in zip(img_names, img_lst):
                io.imsave(os.path.join(new_sub_dir_path, fname), img_arr)

        self.sub_dirs = new_sub_dirs

    def show(self, sub_dir, img_ind):
        """
        View the nth image in the nth class

        :param sub_dir: The name of the category
        :param img_ind: The index of the category of images
        """
        sub_dir_ind = self.label_map[sub_dir]
        io.imshow(self.img_lst2[sub_dir_ind][img_ind])
        plt.show()

    def transform(self, func, params, sub_dir=None, img_ind=None):
        """
        Takes a function and apply to every img_arr in self.img_arr.
        Have to option to transform one as  a test case

        :param func: Function to be applied to each of the images
        :param params: Parameters that go with the function to be applied to each image
        :param sub_dir: The index for the image
        :param img_ind: The index of the category of images
        """
        # Apply to one test case
        if sub_dir is not None and img_ind is not None:
            sub_dir_ind = self.label_map[sub_dir]
            img_arr = self.img_lst2[sub_dir_ind][img_ind]
            io.imshow(func(img_arr, **params).astype(np.uint8))
            plt.show()
        # Apply the function and parameters to all the images
        else:
            new_img_lst2 = []
            for img_lst in self.img_lst2:
                new_img_lst2.append([func(img_arr, **params).astype(np.uint8) for img_arr in img_lst])
            self.img_lst2 = new_img_lst2

    @staticmethod
    def _key_point_dist(key_points, threshold=0.8):
        """
        Takes a list of key points for an image and return a fraction of those that are close together

        :param key_points: Key points identified for an image
        :param threshold: The fraction of key points to include
        :return: A subset of the key points
        """
        key_points = [kp.pt for kp in key_points]
        key_point_pairs = itertools.combinations(key_points, 2)
        kp2dist = defaultdict(list)
        for kp1, kp2 in key_point_pairs:
            dist = euclidean(kp1, kp2)
            kp2dist[kp1].append(dist)
            kp2dist[kp2].append(dist)

        for kp, dist in kp2dist.iteritems():
            kp2dist[kp] = np.mean(dist)

        n = int(len(key_points) * threshold)
        sorted_items = sorted(kp2dist.items(), key=lambda x: x[1])[:n]
        return zip(*sorted_items)[0]

    def _object_crop_one(self, img_arr, obj_detect_class, threshold):
        """
        Accept an image as a numpy array and crop image according key points identified from object detection algo

        :param img_arr: Image as a numpy array
        :param obj_detect_class: An instantiated class with a method `detect()` to detect an object (SIFT)
        :return:
        """
        # Gray scale the image if it has not been grayscaled
        if len(img_arr.shape) > 2:
            gray = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_arr

        key_points = obj_detect_class.detect(gray)
        key_points = self._key_point_dist(key_points, threshold=threshold)
        x, y = zip(*key_points)
        y_min, y_max = min(y), max(y)
        x_min, x_max = min(x), max(x)
        return img_arr[y_min:y_max, x_min:x_max]

    def sift_crop(self, contrast_threshold=0.15, threshold=0.6, sub_dir=None, img_ind=None):
        """
        Apply sift to all images to get key points and crop those image

        :param contrast_threshold: Determine how many key points we are gonna get. Higher = Fewer key points
        :param resize_shape: A tuple of 2 describing the shape of the final image
        :param sub_dir: The sub dir (if you want to test the transformation on 1 image)
        :param img_ind: The index of the image within the chosen sub dir
        """
        sift_detect_class = cv2.xfeatures2d.SIFT_create(contrastThreshold=contrast_threshold)
        # Extract key points and crop a bounding box of the key points
        self.transform(self._object_crop_one,
                       dict(obj_detect_class=sift_detect_class, threshold=threshold),
                       sub_dir=sub_dir, img_ind=img_ind)

    def grayscale(self, sub_dir=None, img_ind=None):
        """
        Grayscale all the images in self.img_lst2

        :param sub_dir: The sub dir (if you want to test the transformation on 1 image)
        :param img_ind: The index of the image within the chosen sub dir
        """
        self.transform(color.rgb2gray, {}, sub_dir=sub_dir, img_ind=img_ind)

    def canny(self, sub_dir=None, img_ind=None):
        """
        Apply the canny edge detection algorithm to all the images in self.img_lst2

        :param sub_dir: The sub dir (if you want to test the transformation on 1 image)
        :param img_ind: The index of the image within the chosen sub dir
        """
        self.transform(feature.canny, {}, sub_dir=sub_dir, img_ind=img_ind)

    def tv_denoise(self, weight=2, multichannel=True, sub_dir=None, img_ind=None):
        """
        Apply to total variation denoise to all the images in self.img_lst2

        :param sub_dir: The sub dir (if you want to test the transformation on 1 image)f
        :param img_ind: The index of the image within the chosen sub dir
        """
        self.transform(restoration.denoise_tv_chambolle,
                       dict(weight=weight, multichannel=multichannel),
                       sub_dir=sub_dir, img_ind=img_ind)

    def resize(self, shape, save=False):
        """
        Resize all images in self.img_lst2 to a uniform shape

        :param shape: A tuple of 2 or 3 dimensions depending on if your images are grayscaled or not
        :param save: Boolean to save the images in new directories or not
        """
        self.transform(transform.resize, dict(output_shape=shape))
        if save:
            shape_str = '_'.join(map(str, shape))
            self.save(shape_str)

    def _vectorize_features(self):
        """
        Take a list of images and vectorize all the images. Returns a feature matrix where each
        row represents an image
        """
        row_tup = tuple(img_arr.ravel()[np.newaxis, :]
                        for img_lst in self.img_lst2 for img_arr in img_lst)
        self.test = row_tup
        self.features = np.r_[row_tup]

    def _vectorize_labels(self):
        """
        Convert file names to a list of y labels (in the example it would be either cat or dog, 1 or 0)
        """
        # Get the labels with the dimensions of the number of image files
        self.labels = np.concatenate([np.repeat(i, len(img_names))
                                      for i, img_names in enumerate(self.img_names2)])

    def vectorize(self):
        """
        Return (feature matrix, the response) if output is True, otherwise set as instance variable.
        Run at the end of all transformations
        """
        self._vectorize_features()
        self._vectorize_labels()
