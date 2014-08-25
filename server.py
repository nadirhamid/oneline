#!/bin/env python

## This file is apart of Oneline's server 
## Nadir Hamid <matrix.nad@gmail.com>

import os
from oneline import ol

if __name__ == '__main__':
	server = ol.server()
	server.start()