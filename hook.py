#!/usr/bin/env python

from ycmd.completers.d.dcd_completer import DCDCompleter

def GetCompleter( user_options ):
  return DCDCompleter( user_options )
