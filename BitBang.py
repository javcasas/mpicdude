'''Bit-bang mode generic controllers

@author     Javier Casas (javcasas AT gmail DOT com)
@version    1.0
'''
__author__ = "Javier Casas (javcasas AT gmail DOT com)"
__version__ = "1.0"

#__docformat__ = "javadoc"

import parallel
import time
import parallel.parallelutil

class BitBangController:
	'''Implements an abstract basic bit-bang controller for programming PIC microcontrollers.'''

	# public members
	mclr = False
	vdd = False
	pgd = False
	pgc = False

	def begin(self):
		'''Initializes any subsystem needed. It must be implemented.'''
		raise NotImplementedError("BitBangController::begin - Not implemented")

	def end(self):
		'''Clears any subsystem needed. It must be implemented.'''
		raise NotImplementedError("BitBangController::end - Not implemented")

	def set_mclr(self, i):
		'''Sets the value of the MCLR line.'''
		self.mclr=i

	def set_vdd(self, i):
		'''Sets the value of the VDD line.'''
		self.vdd=i

	def set_pgd(self, i):
		'''Sets the value of the PGD line.'''
		self.pgd=i

	def set_pgc(self, i):
		'''Sets the value of the PGC line.'''
		self.pgc=i

	def read_pgd(self):
		'''Reads the value of the PGD line. It must be implemented.'''
		raise NotImplementedError("BitBangController::read_pgd - Not implemented")

	def commit(self):
		'''Applies the values set for MCLR, VDD, PGC & PGD to the port. It must be implemented.'''
		raise NotImplementedError("BitBangController::commit - Not implemented")



class BitBangParallel(BitBangController):
	'''Implements an abstract bit-bang controller for programming PIC microcontrollers using the parallel port.'''
	def begin(self):
		'''Creates a new parallel interface.'''
		self.p=parallel.Parallel()

	def end(self):
		'''Deletes its parallel interface.'''
		self.p=None



class BitBangCheapParport(BitBangParallel):
	'''Implements a bit-bang controller for programming PIC microcontrollers using the cheap bit-bang parallel adapter. The lines used are:
	D0 -- PGD
	D1 -- PGC
	D2 -- MCLR
	ACK -- PGD as input	
	'''

	def commit(self):
		'''Applies the values set for MCLR, VDD, PGC & PGD to the port.'''
		mclr = self.mclr << 2
		pgc = self.pgc << 1
		pgd = self.pgd
		registro = mclr | pgc | pgd

		self.p.setData(registro)

	def read_pgd(self):
		'''Sets PGD as 1 and reads the ACK line.'''
		self.set_pgd(1)
		self.commit()
		self.pgd=self.p.getInAcknowledge()
		return self.pgd
