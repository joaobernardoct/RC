import os
import sys


#------1. Paths-------------------------------------------------------------------------------

#This function returns this file's current directory
def app_path():
    return os.getcwd()


#This function returns whether a directory is empty
def is_path_empty(path):
    if not os.listdir(path):
        return True #is empty
    return False #isn't empty


#This function returns the path for a CS/user_nnnnn directory that is maintained by the central server
def cs_user_folder(user):
    path = app_path() + '/CS/user_' + str(user)
    return path


#This function returns the path for a CS/user_nnnnn directory that is maintained by the central server
def bs_user_folder(user):
    path = app_path() + '/BS/user_' + str(user)
    return path


#os.path.isdir(folder_path) para saber se existe o path folder_path

#---------------------------------------------------------------------------------------------



#------2. Folders-----------------------------------------------------------------------------

#This function creates a new directory (path)
def create_folder(path):
    try:
        os.mkdir(path)
    except OSError:
        print '   Creation of the directory %s failed' % path



#This function deletes a directory (path)
def delete_folder(path):
    try:
        os.rmdir(path)
    except OSError:
        print '   Deletion of the directory %s failed' % path

#---------------------------------------------------------------------------------------------



#------3. Txt Files---------------------------------------------------------------------------

#This function creates a new filename.txt in app_path
#  note: it can also be used to overwrite an existing filename.txt file
def create_txt(filename,text):
    file = open(filename, 'w')
    file.write(text)
    file.close()


#This function will append to the end of the filename.txt
def append_txt(filename,text):
    file = open(filename, 'a')
    file.write(text)
    file.close()


#This functions deletes filename.txt
def delete_txt(filename):
    os.remove(filename)   #not tested yet


#This function returns whether filename.txt exists in app_path() directory
def exists_file(filename):
    return os.path.exists(filename)


#This function returns filename.txt first line
def read_first_line(filename):
    file = open(filename, 'r')
    line1 = file.readline()
    file.close()
    return line1
#---------------------------------------------------------------------------------------------
