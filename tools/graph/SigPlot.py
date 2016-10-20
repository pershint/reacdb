from __future__ import print_function
import couchdb
import matplotlib.pyplot as plt
import numpy as np
import sys

couch = couchdb.Server()


def connectToDB(dbName):
    status = "ok"
    db = {}
    try:
        db = couch[dbName]
    except:
        print("Failed to connect to " + dbName, file = sys.stderr)
        status = "bad"
    return status, db

def getSigs():
    """
    Get significance factors for all reactors from reacdb/static.
    The name and significance list are returned as numpy arrays.
    """
    Reac_names = []
    Reac_sigs = []
    dbStatus, db = connectToDB('reacdb')
    if dbStatus is "ok":
        queryresult = db.view('reacdb/static-significance', descending=True)
        for row in queryresult:
            try:
                doc = db[row.id]
                Reac_names.append(doc['reactor_name'])
                Reac_sigs.append(doc['significance_factor'])
            except:
                print("error at" + str(row.id) + "in grabbed query.")
        Reac_names = np.array(Reac_names)
        Reac_sigs = np.array(Reac_sigs)
        return Reac_names, Reac_sigs

def cumulSum(array):
    """
    Takes in an array of numbers and returns an array with the cumulative
    sum values.  Example: cumulSum([2,4,5,7])
    will return [7, 12, 16, 18].
    """
    array = np.sort(array)[::-1] #Sorts any array that's not low to high
    csarray = np.zeros(array.size)
    for i, val in enumerate(array):
        if i == 0:
            csarray[i] = val
        else:
           csarray[i] = csarray[i-1] + val
    print(csarray)
    return csarray

def normalizeArrMax(array):
    """
    Takes in any numpyarray and normalizes it's elements by the largest value.
    """
    largest = np.amax(array)
    for i,entry in enumerate(array):
        array[i] = entry/largest
    print(array)
    return array
        
def normalizeArrSum(array):
    """
    Takes in any numpy array and normalizes all elements by the sum of all values.
    """
    largest = np.sum(array)
    for i,entry in enumerate(array):
        array[i] = entry/largest
    print(array)
    return array

def plotAxes(x,y):
    """
    Takes in two arrays  and plots them in a bar graph.
    The x array should contain the labels for each bar, and the y array
    contains the values for each bar.
    """
    nreacs = len(x)
    bar_width = 0.02
    opacity = 0.4
    fig, ax = plt.subplots()
    plt.gcf().subplots_adjust(bottom=0.2)
    index = np.arange(nreacs)
    plt.bar(index, y, alpha=opacity, color='g')
    plt.xlabel('Reactor Core Name')
    plt.ylabel('% Significance')
    plt.title(r'Cumulative Sum of US/CA Reactor Significances for SNO+' + \
    r'AntiNu flux (~$\frac{MWt}{D^2}$)',y=1.02, fontsize=19)
    plt.xticks(index + bar_width, x, rotation='vertical',y=0.001)
    #plt.legend()
    #plt.tight_layout()  #could use instead of the subplots_adjust line
    plt.show()

if __name__ == '__main__':
    x,y = getSigs()
    #y_n = normalizeArrSum(y)
    #plotAxes(x,y_n)
    #Uncomment to plot cumulative sum
    y_cs = cumulSum(y)
    y_cs = normalizeArrMax(y_cs)
    plotAxes(x,y_cs)
