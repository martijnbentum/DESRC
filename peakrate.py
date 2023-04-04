import glob
from matplotlib import pyplot as plt
import numpy as np
import random
from scipy.io import loadmat


mat_dir = '../MAT/'
fn_mat = glob.glob(mat_dir + '*.mat')

def fid_to_mat(fid):
    for f in fn_mat:
        if fid in f: return load_mat(f)

def block_to_mat(block):
    return fid_to_mat(block.wav_filename.split('.')[0])

def load_mat(filename):
    return loadmat(filename)


def plot_mat(mat,  start=0, end=-1, title = ''):
    plt.ion()
    fig = plt.figure()
    plt.plot(mat['peakEnv'][0][start:end])
    plt.plot(mat['env'][0][start:end])
    plt.plot(mat['peakRate'][0][start:end])
    plt.plot(mat['audio'][0][start:end],alpha = .3)
    if title: plt.title(title)
    plt.legend(['peak envelope','amplitude envelope','peak rate', 'audio'])
    plt.grid(alpha=.1)
    plt.show()
    return fig
    

def plot_word(word):
    start = int(word.st * 1000)
    end = int(word.et * 1000)
    title = 'word: ' + word.word + ' | ' + word.block.wav_filename
    title += ' | ' + str(word.st) + ' - ' + str(word.et)
    mat = block_to_mat(word.block)
    fig = plot_mat(mat, start, end , title)
    return fig, mat

def plot_large_peakrate(block,n_plots = 3, threshold = 0.02):
    mat = block_to_mat(block)
    peakrate = mat['peakRate'][0]
    peak_indices = np.where(peakrate > threshold)[0]
    print('n peakrate events:',len(peak_indices),'above',threshold)
    peak_indices = random.sample(list(peak_indices), n_plots)
    for peak_indice in peak_indices:
        start = peak_indice - 300
        end = peak_indice + 600
        v = str(peakrate[peak_indice])
        t = str(peak_indice/1000)
        plot_mat(mat,start,end,'peakrate | time ' + t + ' | value ')  


