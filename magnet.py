#!/usr/bin/env python
#-*- coding:utf-8 -*-

# random.gauss(mu, sigma)
# Gaussian distribution. mu is the mean, and sigma is the standard deviation.

import sys
import numpy.random as numpyrandom

import psyco
psyco.full()


class Cluster(object):
	# minden klaszer pont(ok)ból készül
	def __init__(self, p):
		self.points = [p, ]
		self.mean = p # alapesteben ez az egy pont a center/átlag

	# két klaszer távolsága
	def mean_distance(self, cluster):
		# euklidészi távolsága a két mean pontnak, gyorsabb sokkal mint a math.sqrt(math.pow(...))
		return ( (self.mean[0]-cluster.mean[0])**2 + (self.mean[1]-cluster.mean[1])**2 ) ** 0.5
	
	# két klaszer összeolvasztása esetén a középpontjuk a két klaszter középpontjának átlaga lesz, ezért ezt nem kell mindig kiszmálonunk
	def add(self, cluster):
		self.mean = [(self.mean[0] + cluster.mean[0])/2, (self.mean[1] + cluster.mean[1])/2]
		self.points[len(self.points):] = cluster.points

	def puts(self):
		for p in self.points:
			print "(%f, %f) " % (p[0], p[1]),
		print


class Agnes(object):

	def __init__(self, clusterlist, output=False):
		self.clusterlist = clusterlist
		self.output = output
	
	
	# a különbozőségi vectort készíti el, klaszterek távolságait tartalmazza
	def generate_dissimilarity(self):
		# pl egy 3 elemu tombnel
		# [0,1] [0,2] [1,2] # magyarul mindenkit mindenkivel, de csak egyszer
		# egy 6 elemű cluster esetén:
		# első sor, első elem távolsága az utána következőktől...stb
		#	[[0.2, 0.3, 0.5, 0.7, 1.6],
		#	 [0.1, 0.1, 0.3, 0.6],
		#	 [0.9, 0.2, 0.2],
		#	 [0.4, 0.3],
		#	 ...
		#	]
		col = []
		for i in xrange(len(self.clusterlist)-1):
			row = []
			for j in xrange(len(self.clusterlist)-i-1):
				row.append( self.clusterlist[i].mean_distance(self.clusterlist[i+j+1]) )
				# pairs.append([i,i+j+1]) # majd ezzel is lehetne spórolni hogy lefoglalok egy tömböt és akkor nem kell majd append, hanem csak[i][stb]
			col.append(row)

		self.dissimilarity = col


	def agnes_step(self):
		
		# ez a clusterek száma aminél majd kiszáll, ezt lehet kapni majd paraméterül
		if len(self.clusterlist) == 1: # ha elértük a végét lépjünk vissza
			return

		#	MIN_DISSIMILARITY megkeresése
		# megkeressük a két legközelebbi klasztert
		# x a beolvasztandó lesz y-ba
		md = min(self.dissimilarity[0]) # minimum dissimilarity - első sor legkisebb eleme
		x,y = 0, self.dissimilarity[0].index(md) # pozíciója a vektorban, FONTOS!!! ez nem egyenlő a clusterlistbeli pozíciójával, le kell képezni
		for i,row in enumerate(self.dissimilarity): # minimum keresés
			rm = min(row)
			if rm < md:
				md = rm
				x,y = i,row.index(rm) # i-edik sor, valahanyadik eleme
		# akkor itt meg van a legkisebb eleme a vectornak, és azt is tudjuk, hogy melyik indexen van a vectorban, de nem a clusterlistben, mer az még nem kell
		# töröljük azt a sort a vekroból ami a beolvasztandó klaszter adatait tartalmazza
		del(self.dissimilarity[x])
		
		# minden sorból kivesszük az x-edik elemhez mért távolságot, persze ennek csak akkor van értelme ha x, nem az első sorban van a dissimilarity-ben
		# és csak x-edik sorig kell elmenni
		#print x,y
		if x != 0:
			i = x-1
			for j in xrange(x):
				del(self.dissimilarity[j][i])
				i -= 1
		#############
		
		y = x+y+1 # leképezés dissimilarity-ből clusterlist dimenzióba, pl x,y = 5,0 => 5,6
		
		# beolvasztás
		# az egyiket kivesszük a listából és beleolvasztjuk a másikba
		clus = self.clusterlist[x]
		self.clusterlist[y].add(clus)
		del(self.clusterlist[x]) # mindenképpen törölni kell
		
		# UPDATE dissimilarity
		# mostmár updatelhetjük az y-tól mért új távolságokat
		# x-edik sort kivettük dissimilarity-ből, és a clusterlistból is, ezért y = y-1
		# csak y-ig kell elmennünk, ugyanis az utána következő elemek nem tartalmazzák a tőle mért távolságot
		y = y-1
		for i in xrange(y):
			self.dissimilarity[i][y-i-1] = self.clusterlist[y].mean_distance(self.clusterlist[i])
		#####################################
		
		# printeljünk ha kell
		if self.output:
			for i, cluster in enumerate(self.clusterlist):
				print i,
				cluster.puts()
			print


# MAIN ############################################
def main():
	
	cov = ((1,2),(3,4)) # egy szimpla kovariancia mátrix
	mean = (10,20) # egy kétdimenziós vektrot ad vissza, 2,2 várható értéke mind a kettőnek

	if len(sys.argv) < 3:
		print "usage: ./agnes.py [NUMBEROFPOINTS] [NUMBEROFCLUSTERS]"
		sys.exit(0)

	num_of_points = int(sys.argv[1])
	num_of_clusters = int(sys.argv[2])

	if num_of_points < 1:
		print "error: wrong number of points, at least 1"
		sys.exit(0)

	if num_of_clusters < 1 or num_of_clusters > num_of_points:
		print "error: wrong number of clusters"
		sys.exit(0)

	print "generating " + str(num_of_points) + " point(s)...",
	sys.stdout.flush()
	
	clusterlist = []
	for i in xrange(num_of_points):
		p = numpyrandom.multivariate_normal(mean,cov)
		clusterlist.append(Cluster(p))
	
	agnes = Agnes(clusterlist, False)

	print "ready\ngenerating dissimilarity vector...",
	sys.stdout.flush()
	agnes.generate_dissimilarity()

	print "ready\nrunning AGNES to create " + str(num_of_clusters) + " cluster(s)...",
	sys.stdout.flush()

	# léptetjük az agnes algoritmust, amíg el nem érjük a kívánt klaszterszámot
	for i in xrange(len(clusterlist)-num_of_clusters):
		agnes.agnes_step()

	print "ready"

#import cProfile
#cProfile.run('main()')

main()

