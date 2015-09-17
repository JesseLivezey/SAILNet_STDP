# -*- coding: utf-8 -*-
"""
Created on Mon Mar 09 22:22:28 2015

@author: Greg
"""

import numpy as np
import theano
import theano.tensor as T
from theano.compat.python2x import OrderedDict
    
class Abs_Learning_Rule(object):
    
    def CalculateChange(self):
        raise NotImplementedError
    
    def Update(self):
        raise NotImplementedError

    def ReduceLearning(self,tt):
        parameters = self.network.parameters
        reduce_learning_rate = parameters.reduce_learning_rate
        
        if tt >= parameters.begin_decay:
            parameters.gamma.set_value(parameters.gamma.get_value() *
                                       reduce_learning_rate)
            parameters.beta.set_value(parameters.beta.get_value() *
                                      reduce_learning_rate)
            parameters.alpha.set_value(parameters.alpha.get_value() *
                                       reduce_learning_rate)
            
class Learning_Rule(Abs_Learning_Rule):
    
    def __init__(self, network, dW_rule):
        self.network = network
        parameters = network.parameters
        updates = OrderedDict()
        X = network.X
        beta = parameters.beta
        gamma = parameters.gamma
        batch_size = parameters.batch_size
        p = parameters.p
        time_data = parameters.time_data
        rnd = theano.tensor.shared_randomstreams.RandomStreams()
        
        for layer_num in range(network.n_layers):
            Y = network.Y[layer_num]
            Q = network.Q[layer_num]
            W = network.W[layer_num]
            theta = network.theta[layer_num]

            """
            Calculate Change in Feed-Forward Weights dQ
            """        
            square_act = T.sum(Y*Y,axis=0)
            mymat = T.diag(square_act)
            dQ = beta*(X.T.dot(Y) - (Q.dot(mymat)))/batch_size        
            Q = Q+dQ    
            
            if time_data:
                time_overlap = rnd.random_integers(low=0,high=50)
            
                spike_train = T.concatenate((spike_train_tm1[:,:,-time_overlap:],
                                          spike_train[:,:,:(50-time_overlap)])
                                          ,axis=2)
                Y = T.sum(spike_train,axis=2)

            dW_Rule = str_to_dW[dW_rule](network)
            
            dW = dW_Rule.calc_dW(layer_num)
            
            #mag_dW = T.sqrt(T.sum(T.sqr(dW)))
    
            W = W+dW
            W = W - T.diag(T.diag(W))
            W = T.switch(W < 0.,0.,W)
            
            """
            Calculate Change in Threshold Weights dtheta
            """        
            muy = Y.mean(axis=0)
            dtheta = gamma*(muy - p)
            theta = theta+dtheta
    
            updates[network.Q[layer_num]] = Q
            updates[network.W[layer_num]] = W
            updates[network.theta[layer_num]] = theta            
            
            #Setting input of next layer to spikes of current one
            X = Y
        
        self.f = theano.function([], [], updates=updates)
        
    def Update(self):
        self.network.next_trial()
        self.f()
        
"SAILNet Rule and Time Dependent Rules for dW"
        
class Abs_dW(object):
    
    def __init__(self,network):
        self.network = network

class dW_SAILnet(Abs_dW):
    
    def calc_dW(self,layer_num):
        
        Y = self.network.Y[layer_num]
        alpha = self.network.parameters.alpha
        batch_size = self.network.parameters.batch_size
        p = self.network.parameters.p
        
        Cyy = Y.T.dot(Y)/batch_size
        dW = alpha*(Cyy - p**2)
        
        dW=dW.astype('float32')

        return dW
    
class dW_identity(Abs_dW):
    
    def calc_dW(self, layer_num):
        spike_train = self.network.spike_train[layer_num]
        batch_size = self.network.parameters.batch_size
        num_iterations = self.network.parameters.num_iterations  
        p = self.network.parameters.p
        alpha = self.network.parameters.alpha        
        
        min_constant = p**2/num_iterations
        dW = T.tensordot(spike_train, spike_train, axes=([0, 2], [0, 2]))
        
        dW = dW/batch_size
        dW = alpha*(p**2*dW/min_constant - p**2)
        
        return dW
        
class dW_time_dep(Abs_dW):
    
    def __init__(self,network):
        super(dW_time_dep,self).__init__(network)
        network.time_dep = time_matrix(str_to_fnc[network.parameters.function],self.network.parameters.num_iterations)
        
    def calc_dW(self,layer_num):
        spike_train = self.network.spike_train[layer_num]
        batch_size = self.network.parameters.batch_size
        num_iterations = self.network.parameters.num_iterations  
        p = self.network.parameters.p
        alpha = self.network.parameters.alpha  
        
        P = p*np.ones(num_iterations,dtype= 'float32')
        min_constant = np.array(np.dot(P,np.dot(self.network.time_dep.get_value(),P))/num_iterations**2, dtype='float32')
        
        dW = T.tensordot(spike_train,self.network.time_dep,axes=([2],[0]))
        dW = T.tensordot(dW, spike_train,axes=([0,2],[0,2]))        
        
        dW = dW/batch_size  
        dW = alpha*(p**2*dW/min_constant - p**2)

        return dW
        
str_to_dW = {'dW_SAILnet': dW_SAILnet,
             'dW_identity': dW_identity,
             'dW_time_dep': dW_time_dep}
    
def time_matrix(function,iterations):
    
    time_dep= np.zeros((iterations,iterations))
    for i in xrange(iterations):
        for j in xrange(iterations):

            time_dep[i][j] = function(i,j)
                
    return theano.shared(time_dep.astype('float32'))  
        
        
"Time Dependent Functions"

def STDP(i,j):
    post_activity=-2.7
    pre_activity= 27 
    time_scale=2
    
    dt = i-j
    if np.sign(dt) == 1:
        return pre_activity*np.exp(-abs(dt*time_scale))*(dt)**16
    else:
        return post_activity*np.exp(-abs(dt*time_scale))*(dt)**16
    
def Unit(i,j): #Same as vanilla SAILNet
    return 1
    
def Step(i,j):
    dt = i-j
    step_len = 10
    step_height = 1
    if abs(dt) <= step_len/2:
        return step_height
    else:
        return 0
        
def Well(i,j):
    dt = i-j
    length = 10
    depth = 1
    if abs(dt) <= length/2:
        return 0
    else:
        return depth

def Gaussian(i,j):
    std = 5
    dt = i-j
    return np.exp(-0.5*(dt/std)**2)

def Negative(i,j):
    return -1

def Linear15(i,j):
    dt = i-j
    width = 15.
    if abs(dt) <= width:
        return dt/width
    else:
        return 0

def Double_Gaussian(i,j):
    std = 1
    off_set = 5
    dt = i-j
    return np.exp(-0.5*((dt+off_set)/std)**2)+ np.exp(-0.5*((dt-off_set)/std)**2)

   
str_to_fnc = {'STDP': STDP,
              'Unit': Unit,
              'Step': Step,
              'Well': Well,
              'Gaussian': Gaussian,
              'Negative': Negative,
              'Linear15': Linear15,
              'Double_Gaussian':Double_Gaussian}        
