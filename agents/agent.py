import numpy as np
import sys
#sys.path.append('./model')
from agents.core import get_all_childs

n_actions = 6

class Agent:

    def __init__(self,sims,init_nodes=500000,backend='tensorflow'):

        self.sims = sims
        
        self.init_nodes = init_nodes
        self.backend = backend

        self.init_array()
        self.init_model()

    def init_array(self):

        child_arr = np.zeros((self.init_nodes,n_actions),dtype=np.int32)
        node_stats_arr = np.zeros((self.init_nodes,5),dtype=np.float32)

        self.arrs = {
                'child':child_arr,
                'node_stats':node_stats_arr,
                }

        self.game_arr = [None] * self.init_nodes

        self.available = [i for i in range(1,self.init_nodes)]
        self.occupied = [0]

        self.node_index_dict = dict()

        self.max_nodes = self.init_nodes

    def init_model(self):

        if self.backend == 'tensorflow':
            from model.model import Model
            import tensorflow as tf

            self.sess = tf.Session()
            
            self.model = Model()
            self.model.load(self.sess)
            
            self.inference = lambda state: self.model.inference(self.sess,state[None,:,:,None])

        elif self.backend == 'pytorch':
            from model.model_pytorch import Model
            self.model = Model()
            self.model.load()

            self.inference = lambda state: self.model.inference(state[None,None,:,:])

        else:
            self.model = None

    def evaluate(self,node):

        state = node.game.getState()

        return self.evaluate_state(state)

    def evaluate_state(self,state):

        v, p = self.inference(state)
            

        return v[0][0], p[0]

    def expand_nodes(self,n_nodes=10000):

        sys.stdout.write('Adding more nodes...\n')
        sys.stdout.flush()

        for k, arr in self.arrs.items():
            _s = arr.shape
            _new_s = [_ for _ in _s]
            _new_s[0] = n_nodes
            _temp_arr = np.zeros(_new_s,dtype=arr.dtype)
            self.arrs[k] = np.concatenate([arr,_temp_arr])

        self.game_arr += [None] * n_nodes
        self.available += [i for i in range(self.max_nodes,self.max_nodes+n_nodes)]
        self.max_nodes += n_nodes

    def new_node(self,game):

        if game in self.node_index_dict:

            return self.node_index_dict[game]

        else:

            if self.available:
                idx = self.available.pop()
            else:
                self.remove_nodes()
                if self.available:
                    idx = self.available.pop()
                else:
                    self.expand_nodes()
                    idx = self.available.pop()

            _g = game.clone()

            self.node_index_dict[_g] = idx

            self.game_arr[idx] = _g

            self.occupied.append(idx)

            return idx

    def mcts(self,root_index):
        pass

    def play(self):

        for i in range(self.sims):
            self.mcts(self.root)

        self.stats = self.compute_stats()

        if np.all(self.stats[3] == 0):
            action = np.random.choice(n_actions)
        else:
            action = np.argmax(self.stats[3])

        return action

    def compute_stats(self):

        _stats = np.zeros((6,n_actions))

        _childs = self.arrs['child'][self.root]
        _ns = self.arrs['node_stats']

        for i in range(n_actions):
            _idx = _childs[i]
            _stats[0][i] = _ns[_idx][0]
            _stats[1][i] = _ns[_idx][1]
            _stats[2][i] = 0
            _stats[3][i] = _ns[_idx][1] / _ns[_idx][0]
            _stats[4][i] = _ns[_idx][3]
            _stats[5][i] = _ns[_idx][4]

        return _stats

    def get_prob(self):

        return self.stats[0] / np.sum(self.stats[0])

    def get_stats(self):

        return self.stats

    def remove_nodes(self):

        _c = get_all_childs(self.root,self.arrs['child'])

        self.occupied = list(_c)

        self.available = list(set(range(self.max_nodes)) - _c)

        for idx in self.available:
            _g = self.game_arr[idx]

            del self.node_index_dict[_g]

            self.game_arr[idx] = None

            self.arrs['child'][idx] = 0
            self.arrs['node_stats'][idx] = 0

    def set_root(self,game):

        self.root = self.new_node(game)

    def update_root(self,game):

        self.set_root(game)


