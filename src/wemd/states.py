'''
Created on Feb 10, 2012

@author: mzwier
'''

from __future__ import division; __metaclass__ = type

import numpy

class BasisState:
    '''Describes an basis (micro)state. These basis states are used to generate
    initial states for new trajectories, either at the beginning of the simulation
    (i.e. at w_init) or due to recycling.

    :ivar state_id:     Integer identifier of this state, usually set by the
                        data manager.
    :ivar label:        A descriptive label for this microstate (may be empty)
    :ivar probability:  Probability of this state to be selected when creating a
                        new trajectory.
    :ivar pcoord:       The representative progress coordinate of this state.
    
    :ivar auxref:       A user-provided (string) reference for locating data associated
                        with this state (usually a filesystem path).
    '''
    def __init__(self, label, probability, pcoord=None, auxref=None, state_id=None):
        self.label = label
        self.probability = probability         
        self.pcoord = numpy.atleast_1d(pcoord)
        self.auxref = auxref 
        self.state_id = state_id
        
    def __repr__(self): 
        return ('{} state_id={self.state_id!r} label={self.label!r} prob={self.probability!r} pcoord={self.pcoord!r}>'
                .format(object.__repr__(self)[:-1], self=self))
        
    @classmethod
    def states_from_file(cls, filename):
        '''Read a file defining basis states.  Each line defines a state, and contains a label, the probability, 
        and optionally a data reference, separated by whitespace, as in::
        
            unbound    1.0
        
        or::
            
            unbound_0    0.6        state0.pdb
            unbound_1    0.4        state1.pdb
        
        '''
        states = []
        lineno = 0
        for line in file(filename, 'rt'):
            lineno += 1
            
            # remove comment portion
            line = line.partition('#')[0].strip()
            if not line:
                continue
            
            fields = line.split()
            label = fields[0]
            try:
                probability = float(fields[1])
            except ValueError:
                raise ValueError('invalid probability ({!r}) {} line {:d}'.format(fields[1], filename, lineno))
            
            try:
                data_ref = fields[2].strip()
            except IndexError:
                data_ref = None
                
            states.append(cls(state_id=None,probability=probability,label=label,data_ref=data_ref))
        return states
    
class InitialState:
    '''Describes an initial state for a new trajectory. These are generally constructed by
    appropriate modification of a basis state. 

    :ivar state_id:         Integer identifier of this state, usually set by the
                            data manager.
    :ivar basis_state_id:   Identifier of the basis state from which this state was
                            generated.
    :ivar basis_state:      The `BasisState` from which this state was generated.
    :ivar iter_gen:         Iteration in which this state was generated (0 for
                            simulation initialization).
    :ivar iter_used:        Iteration in which this state was used to initiate a
                            trajectory (None for unused).
    :ivar pcoord:       The representative progress coordinate of this state.
    '''
    def __init__(self, state_id, basis_state_id, iter_created, iter_used=None, pcoord=None, basis_state=None):
        self.state_id = state_id
        self.basis_state_id = basis_state_id
        self.basis_state=basis_state
        self.iter_created = iter_created
        self.iter_used = iter_used         
        self.pcoord = pcoord
        
    def __repr__(self): 
        return ('{} state_id={self.state_id!r} basis_state_id={self.basis_state_id!r} iter_created={self.iter_created!r}>'
                .format(object.__repr__(self)[:-1], self=self))

class TargetState:
    '''Describes a target state.
    
    :ivar state_id:     Integer identifier of this state, usually set by the
                        data manager.
    :ivar label:        A descriptive label for this microstate (may be empty)
    :ivar pcoord: The representative progress coordinate of this state.
    
    '''
    def __init__(self, label, pcoord, state_id=None):
        self.label = label
        self.pcoord = numpy.atleast_1d(pcoord)
        self.state_id = state_id
        
    def __repr__(self): 
        return ('{} state_id={self.state_id!r} label={self.label!r} pcoord={self.pcoord!r}>'
                .format(object.__repr__(self)[:-1], self=self))
    
    @classmethod
    def states_from_file(cls, statefile, dtype):
        '''Read a file defining target states.  Each line defines a state, and contains a label followed
        by a representative progress coordinate value, separated by whitespace 
        and optionally a data reference, separated by whitespace, as in::
        
            bound     0.02
        
        for a single target and one-dimensional progress coordinates or::
            
            bound    2.7    0.0
            drift    100    50.0
        
        for two targets and a two-dimensional progress coordinate.
        '''
        
        targets = numpy.atleast_1d(numpy.genfromtxt(statefile, dtype=None))
        pcoord_values = numpy.empty((len(targets),), dtype)
        labels = [target[0] for target in targets]
        
        if hasattr(dtype, 'fields'):
            s = numpy.s_[1:]
        else:
            s = numpy.s_[1]
            
        for i, target in enumerate(targets):
            pcoord_values[i] = target[s]
            
        if pcoord_values.ndim == 1:
            pcoord_values.shape = (pcoord_values.shape[0], 1)
            
        return [cls(label=label, pcoord=pcoord) for label,pcoord in zip(labels,pcoord_values)]

def pare_basis_initial_states(basis_states, initial_states, segments=None):
    '''Given iterables of basis and initial states (and optionally segments that use them),
    return minimal sets (as in __builtins__.set) of states needed to describe the history of the given 
    segments an initial states.'''
    
    bstatemap = {state.state_id: state for state in basis_states}
    istatemap = {state.state_id: state for state in initial_states}
    
    if segments is not None:
        segments = list(segments)
        return_bstates = set(bstatemap[segment.p_parent_id] for segment in segments
                             if segment.initpoint_type == segment.SEG_INITPOINT_BASIS)
        return_istates = set(istatemap[segment.p_parent_id] for segment in segments 
                             if segment.initpoint_type == segment.SEG_INITPOINT_GENERATED)
        return_bstates.update(bstatemap[istate.basis_state_id] for istate in return_istates)
    else:
        return_istates = set(initial_states)
        return_bstates = set(bstatemap[istate.basis_state_id] for istate in return_istates)
        
    return return_bstates, return_istates
