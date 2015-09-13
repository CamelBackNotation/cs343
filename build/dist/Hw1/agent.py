from OpenNero import *
from common import *
import sys

import Maze
from Maze.constants import *
import Maze.agent
from Maze.agent import *


def manhattan_heuristic(r, c):
	return abs(ROWS - 1 - r) + abs(COLS - 1 - c)


def get_action_index(move):
	if move in MAZE_MOVES:
		action = MAZE_MOVES.index(move)
		print 'Picking action', action, 'for move', move
		return action
	else:
		return None


class IdaStarSearchAgent(SearchAgent):
	"""
    IDA* algorithm
    """

	def __init__(self):
		# this line is crucial, otherwise the class is not recognized as an AgentBrainPtr by C++
		SearchAgent.__init__(self)
		# fval key: (a, b) val: f-value
		self.fvals = {}
		self.visited = set([])
		self.adjlist = {}
		self.parents = {}
		self.heuristic = manhattan_heuristic
		self.cutoff = 0  # heuristic of starting position
		self.starting_pos = (0, 0)
		self.old_cutoff = sys.maxint
		self.next_cutoff = sys.maxint

	def reset(self):
		"""
        Reset the agent
        """
		pass

	def initialize(self, init_info):
		"""
        Initializes the agent upon reset
        """
		self.action_info = init_info.actions
		return True

	def start(self, time, observations):
		"""
        Called on the first move
        """
		r = observations[0]
		c = observations[1]
		self.cutoff = self.heuristic(r, c)
		# return action
		self.starting_pos = (r, c)
		get_environment().mark_maze_white(r, c)
		return self.act(observations)

	def act(self, time, observations, reward):
		"""
        Called every time the agent needs to take an action
        """
		r = observations[0]
		c = observations[1]
		# debugging purposes
		d = self.get_distance(r, c)
		h = self.heuristic(r, c)
		f = d + h
		current_cell = (r, c)
		# if f > self.cutoff:
		# go back

		self.fvals[current_cell] = f
		print "Current cell D: %d  H: %d  F: %d" % (d, h, f)
		# if we have not been here before, build a list of other places we can go
		if current_cell not in self.visited:
			tovisit = []
			for m, (dr, dc) in enumerate(MAZE_MOVES):
				r2, c2 = r + dr, c + dc
				if not observations[2 + m]:  # can we go that way?
					if (r2, c2) not in self.visited:
						f = self.heuristic(r2, c2) + d + 1
						self.fvals[(r2, c2)] = f
						tovisit.append((r2, c2))
						self.parents[(r2, c2)] = current_cell
			# remember the cells that are adjacent to this one
			self.adjlist[current_cell] = tovisit
		# if we have been here before, check if we have other places to visit
		adjlist = self.adjlist[current_cell]
		# sort adjlist from smallest f value to largest f value
		sorted(adjlist, key=lambda x: self.fvals[x])
		# print adjlist
		print {self.fvals[x] for x in adjlist}
		k = 0
		while k < len(adjlist) and (
				adjlist[k] in self.visited or self.fvals[adjlist[k]] > self.cutoff):
			if (self.fvals[current_cell] < self.fvals[adjlist[k]] < self.next_cutoff):
				self.next_cutoff = self.fvals[adjlist[k]]
				print "next_cutoff: %d" % self.next_cutoff
			print "next_cutoff: %d" % self.next_cutoff
			k += 1
		# if we don't have other neighbors to visit, back up
		if k == len(adjlist):
			if current_cell == self.starting_pos:
				next_cell = adjlist[0]
				self.visited = set([])
				get_environment().cleanup()
				get_environment().mark_maze_white(r, c)
				print "Should be setting cutoff to next_cutoff %d" % self.next_cutoff
				self.cutoff += 2
				# self.cutoff = self.next_cutoff
				# self.next_cutoff = sys.maxint
			else:
				next_cell = self.parents[current_cell]
				# self.visited.discard(next_cell)
		else:  # otherwise visit the next place
			next_cell = adjlist[k]
		self.visited.add(current_cell)  # add this location to visited list
		if current_cell != self.starting_pos:
			get_environment().mark_maze_blue(r, c)  # mark it as blue on the maze
		dr, dc = next_cell[0] - r, next_cell[1] - c  # the move we want to make
		action = get_action_index((dr, dc))
		v = self.action_info.get_instance()  # make the action vector to return
		if action is not None and observations[2 + action] == 0:
			v[0] = action # if yes, do that action!
		else:
			# get_environment().teleport(self, r2, c2)
			v[0] = MAZE_NULL_MOVE
		# remember how to get back
		if next_cell not in self.backpointers:
			# self.backpointers[next_cell] = (current_cell[0], current_cell[1])
			self.backpointers[next_cell] = current_cell
		print "Cutoff: %d" % self.cutoff
		return v

	def mark_path(self, r, c):
		get_environment().mark_maze_white(r, c)

	def end(self, time, reward):
		"""
        at the end of an episode, the environment tells us the final reward
        """
		print  "Final reward: %f, cumulative: %f" % (reward[0], self.fitness[0])
		self.reset()
		return True

	def destroy(self):
		"""
        After one or more episodes, this agent can be disposed of
        """
		return True
