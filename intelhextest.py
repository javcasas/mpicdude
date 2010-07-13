# -*- coding: utf-8 -*-

import intelhex
import sys
class extractor24bits:

	def __init__(self, hex):
		self.mihex=hex

	def extrae_direcciones(self):
		dirs = self.mihex.addresses()
		res=[]
		for dir in dirs:
			if (dir & 0x3) == 3:
				res.append(dir >> 2)
		return res

	def make_slices(self):
		dirs = self.extrae_direcciones()
		res = []
		inicial =0
		final = 0
		anterior = -1
		for dir in dirs:
			if dir == anterior + 1:
				final = dir
			else:
				res.append((inicial, final))
				inicial = final = dir

			anterior = dir

		res.append((inicial, final))

		if res[0] == (0,0):
			res.remove((0,0))

		return res

	def __getitem__(self, addr):
		dir = addr << 2
		val = self.mihex[dir + 3]
		val |= self.mihex[dir + 2] << 8
		val |= self.mihex[dir + 1] << 16
		return val

	def __setitem__(self, addr, bits):
		dir = addr << 2
		self.mihex[dir + 3]= bits & 0xff
		self.mihex[dir + 2]= (bits & 0xff00) >> 8
		self.mihex[dir + 1]= (bits & 0xff0000) >> 16
		self.mihex[dir] = 0x00

def swapHex(hex):
	fixed=intelhex.IntelHex()
	dirs = hex.addresses()
	for dir in dirs:
		final = dir & 0x3
		nwaddr = dir & 0xfffffffc
		if final == 0:
			nwaddr |= 3
			fixed[nwaddr] = hex[dir]
		elif final == 1:
			nwaddr |= 2
			fixed[nwaddr] = hex[dir]
		elif final == 2:
			nwaddr |= 1
			fixed[nwaddr] = hex[dir]
		elif final == 3:
			nwaddr |= 0
			fixed[nwaddr] = hex[dir]
			#fixed[nwaddr] = 0x00
		else:
			print "Fallo"
			sys.exit()

	return fixed


def test1():
	mihex=intelhex.IntelHex()
#	mihex.loadhex('C:/Documents and Settings/Usuario/Escritorio/testpic/1.hex')
	mihex.loadhex('C:/Documents and Settings/Usuario/Escritorio/test.hex')
	mihex16=intelhex.IntelHex16bit(mihex)
	dirs= mihex.addresses()
	max=25
	i=0
	for dir in dirs:
		print hex(dir), hex(mihex[dir])
		i = i+1
		if i > max:
			break
		#print ""
	fixed = swapHex(mihex)
	#print fixed.dump()

	ex=extractor24bits(fixed)
	print ex.extrae_direcciones()
	
	print ex.make_slices()

	print hex(ex[8])
	ex[8] = 0xabcdef
	print hex(ex[8])

	print fixed.dump()

	unfixed = swapHex(fixed)
	print unfixed.dump()

	unfixed.tofile('C:/Documents and Settings/Usuario/Escritorio/test2.hex', "hex")


def main():

	test1()

if __name__ == "__main__":
    main()
