import numpy as np
import math

class FlyController:
    def __init__(self, sim, drones_list):
        self.sim = sim
        self.drones_list = drones_list
        self.n_drones = len(drones_list)

        # define the three basic matrices as zero matrices
        self.matrix_delta = np.zeros((self.n_drones, self.n_drones))
        self.matrix_adj = np.zeros((self.n_drones, self.n_drones))
        self.matrix_laplacian = np.zeros((self.n_drones, self.n_drones))

        # define the min-max distance in meters between the drones
        self.dist_max = 3
        self.dist_min = 0.5

        # define a matrix to store the inter-drone distances of our formation, by default all dist < dmax
        # --> we get a full connected graph
        self.matrix_interdrones_distance = np.full((self.n_drones, self.n_drones), (self.dist_max - 1))

    def update_matrices(self):

        # reset the three basic matrices at each iteration
        self.matrix_delta = np.zeros((self.n_drones, self.n_drones))
        self.matrix_adj = np.zeros((self.n_drones, self.n_drones))
        self.matrix_laplacian = np.zeros((self.n_drones, self.n_drones))

        ### this part is usefull only if we decide that our drones have limited communication range ###
        # define the adjacency matrix as matrix where the i-j th element is = 1 if i and j elements are neighbours
        for i in range(self.n_drones):
            for j in range(self.n_drones):
                # checks if the i-th drone is sufficiently near to the j drones
                if self.matrix_interdrones_distance[i][j] <= self.dist_max:
                    self.matrix_adj[i][j] = 1

        # define delta as matrix where the diagonal elements are = to the degree of node i
        # degree = number of connections of the node
        for i in range(self.n_drones):
            for j in range(self.n_drones):
                self.matrix_delta[i][i] += self.matrix_adj[i][j]

        # calculate the laplacian matrix using the formula L = delta -adj
        self.matrix_laplacian = np.subtract(self.matrix_delta, self.matrix_adj)
        # print("laplacian: ", self.matrix_laplacian)
        return self.matrix_laplacian, self.matrix_delta

    def compute_drone_actual_config_matrix(self):
        ### we need to decide if we want to pick data from a central server or talking directly with other obj !!!!!!!!!!!!
        ### if we decide for the distributed approach, we must implement something to use the delta matrix to understand which are the near drones at which each drone can talk

        # we want the matrix in this form
        # mat = [
        #     [x1, y1, z1, q11, q12, q13, q14]
        #     [x2, y2, z2, q12, q23, q23, q24]
        #     [x3, y3, z3, q31, q32, q33, q34]
        #     ]

        # reset matrix at each iteration
        matrix_drone_config = []

        # iteratively ask each drone its actual config and save it as a matrix where each line contains a drone config
        for i in range(self.n_drones):
            pos, orientation = self.drones_list[i].get_drone_config_info()
            matrix_drone_config.append(pos + orientation)

        return matrix_drone_config

    def consensus_protocol(self, var_to_sync: np.array):
        # il consensus MUST concern itself only around the calculus of the input var's changing ratio

        # var_to_sync MUST be a matrix [n_drones][7]
        z = var_to_sync

        # compute matrices for this time step
        ### momentaneamente non utilizzato, finchè non sarà chiaro come modificare le Wij della mat ADJ ###
        # lap, delta = self.update_matrices()

        # define z_t as my next step configuration
        z_dot = []
        z_dot = np.dot(self.matrix_laplacian, z)

        # round the values of z_t to their third decimal value, to prevent the over-usage of the consensus
        # and the consequential divergence due to approximation errors
        z_dot = np.round(z_dot, 3)

        return z_dot

    def rendezvous_protocol(self, delta_t, target_config: list[7]):
        # compute actual drones position as numpy array
        matrix_drone_config = np.array(self.compute_drone_actual_config_matrix())

        ### per il momento crea le matrici con questa funzione anche se ADJ e LAP non vanno bene
        ### poi le correggi con le righe di codice sotto
        self.update_matrices()

        for i in range(self.n_drones):
            for j in range(self.n_drones):
                if i != j:
                    ### chiedi al prof come definire wij per fare si che i tuoi droni confluiscano nella target config e non nella config intermedia ###
                    # self.matrix_adj[i][j] = pow(np.linalg.norm(target_config[j] - matrix_drone_config[i][j]), 2)
                    self.matrix_adj[i][j] = 1

        print("adj: ", np.round(self.matrix_adj, 3))
        self.matrix_laplacian = np.subtract(self.matrix_delta, self.matrix_adj)

        # computing the new target configs using the consensus protocol to compute the error rate
        # lap,adj = self.update_matrices()
        rate = np.dot(delta_t, self.consensus_protocol(matrix_drone_config))
        print("rate = ", np.round(rate, 3))
        new_drone_targets_config = np.subtract(matrix_drone_config, rate)

        new_drone_targets_config = np.round(new_drone_targets_config, 3)
        print("new config: ", new_drone_targets_config)
        # converting the numpy array into a normal one
        return new_drone_targets_config.tolist()

    def formation_control(self):
        pass
