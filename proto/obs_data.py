#!/usr/bin/python
#! encoding: UTF8
__author__ = 'kirienko'

import datetime as dt
import re

c = 299792428                           # speed of light
nu_1_G, nu_2_G = 1575.42e6, 1227.6e6    # GPS L1 and L2 frequencies
l1_G, l2_G = c/nu_1_G, c/nu_2_G






class ObsGPS():
    def __init__(self, data, obs_types):
        self.raw_data = data
        self.obs_types = obs_types
        self.obs_types_number = len(obs_types)
        self.sat_count = int(data[0][30:32])    # <-- equal to the number of measurements
        if self.sat_count > 12:
            # concatenate lines 0 and one in ```raw_data```:
            self.raw_data[0] = " " + self.raw_data[0].strip() + self.raw_data[1].strip()
            self.raw_data.remove(self.raw_data[1])
        self.sat_types = self.raw_data[0][32:].strip().replace(' ', '0')
        self.PRN_number = [self.sat_types[i*3:(i+1)*3] for i in xrange(self.sat_count)]

        # Time of the observation       TODO: move to helper file
        str_date = data[0].split()[:6]
        if int(str_date[0]) < 2000:
            str_date[0] = '20'+str_date[0]
        sec_msec = "%.6f" % float(str_date[-1])
        s, ms = map(int,sec_msec.split('.'))
        self.date = dt.datetime(*(map(int,str_date[:-1])+[s, ms]))

        # Pseudoranges etc

        def col(matr,i):
                """
                Returns i-th column of a matrix
                :param matr: some matrix of RINEX observation
                :param i: number of a column
                :return:
                """
                return [matr[j][16*i:16*i+14] for j in xrange(len(matr))]

        def is_def(x):
                """
                If this measurement exists
                """
                try:
                    ans = float(x)
                except ValueError:
                    # print "xxx:",re.match('\s+',x)
                    ans = None
                return ans

        self.obs_data = dict((d,[is_def(x) for x in col(self.raw_data[1:], i)])
                             for i,d in enumerate(self.obs_types))

    def prn(self, PRN):
        return self.PRN_number.index(PRN)

    @staticmethod
    def __ionofree(f1,f2,p1,p2):
        '''
        :param f1: L₁ frequency value
        :param f2: L₂ frequency value
        :param p1: Pseudorange P₁ itself or distance L₁λ₁
        :param p2: Pseudorange P₂ itself or distance L₂λ₂
        :return: Ionosphere free pseudorange
        '''
        return (f1*f1*p1-f2*f2*p2)/(f1*f1-f2*f2)

    def ionofree_pseudorange(self, sat_PRN):
        needs = ['C1','P2']
        if None not in [self.obs_data[k][self.prn(sat_PRN)] for k in needs]:
            return self.__ionofree(nu_1_G,nu_2_G,*[self.obs_data[k][self.prn(sat_PRN)] for k in needs])



    def pseudorange(self, sat_PRN, obs_type): #TODO: do we need this?
        '''

        :param sat_PRN: PRN of the satellite (e.g. 'G21')
        :param obs_type: type of observation (e.g. 'C1')
        :return: pseudorange (in meters) corresponding PRN and type of observation
        '''
        if obs_type in self.obs_types and sat_PRN in self.PRN_number:
            return self.obs_data[obs_type][self.prn(sat_PRN)]
        else:
            return None

if __name__ == "__main__":
    with open('../test_data/test.o') as fd:
        data = fd.readlines()

    header_end_marker = "END OF HEADER"
    for j,d in enumerate(data):
        if header_end_marker in d:
            header_end = j
    header, body = data[:header_end],data[header_end+1:]

