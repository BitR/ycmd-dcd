#!/usr/bin/env python3

import os
from queue import Queue
from nose.tools import eq_, raises
from ycmd.completers.d.dcd_completer import DCDCompleter
from ycmd.request_wrap import RequestWrap
from ycmd import user_options_store

TEST_DIR = os.path.dirname( os.path.abspath( __file__ ) )
DATA_DIR = os.path.join( TEST_DIR, 'testdata' )
PATH_TO_TEST_FILE = os.path.join( DATA_DIR, 'test.d' )
# Use test file as dummy binary
DUMMY_BINARY = '/tmp/tool'
PATH_TO_OUTPUT_FILE = os.path.join( DATA_DIR, 'output.txt' )

REQUEST_DATA = {
  'filepath' : PATH_TO_TEST_FILE,
  'file_data' : { PATH_TO_TEST_FILE : { 'filetypes' : [ 'd' ] } }
}

class DCDCompleter_test( object ):
  def setUp( self ):
    user_options = user_options_store.DefaultOptions()
    self._completer = DCDCompleter( user_options )

  def _BuildRequest( self, line_num, column_num ):
    request = REQUEST_DATA.copy()
    request[ 'column_num' ] = column_num
    request[ 'line_num' ] = line_num
    with open( PATH_TO_TEST_FILE, 'r') as testfile:
      request[ 'file_data' ][ PATH_TO_TEST_FILE ][ 'contents' ] = (
        testfile.read() )
    return RequestWrap( request )

  def ComputeCandidates_test( self ):
    self._completer._binary = DUMMY_BINARY
    with open( PATH_TO_OUTPUT_FILE, 'rb' ) as outputFile:
      output = outputFile.read()
    mock = MockPopen( stdout=output )
    self._completer._popener = mock
    request = self._BuildRequest(0, 0)
    self._completer.OnFileReadyToParse(request)
    result = self._completer.ComputeCandidates(request)[0:1]

    eq_( result, [ {
        'menu_text': 'abs (doc)',
        'insertion_text': 'abs',
        'kind': 'f',
        'detailed_info': output.decode('utf-8').strip()}
      ] )

class MockPipe(object):
  def __init__(self, contents=None):
    self.data = ''
    self.shouldRaise = False
    self.lines = []
    if contents:
      self.lines = contents.splitlines()
    self.line = 0

  def raiseOnUse(self):
    self.shouldRaise = True

  def readline(self):
    if self.shouldRaise:
      raise IOError()

    if not self.hasdata():
      return None

    self.line += 1
    return self.lines[self.line - 1] + b'\n'

  def read(self):
    line = self.readline()
    data = b''
    while line:
      data += line
      line = self.readline()
    return data

  def write(self, data):
    if self.shouldRaise:
      raise IOError()

    self.data += data

  def flush(self):
    if self.shouldRaise:
      raise IOError()

  def hasdata(self):
    return self.line < len(self.lines)

class MockSubprocess( object ):
  def __init__( self, returncode, stdout, stderr ):
    self.returncode = returncode
    self.stdout = MockPipe(stdout)
    self.stderr = MockPipe(stderr)
    self.stdin = MockPipe()

  def communicate( self, stdin=None ):
    self.stdin = stdin
    return ( self.stdout.read(), self.stderr.read() )

  def poll(self):
    if self.stdout.hasdata() and self.returncode == None:
      return None
    self.returncode = self.returncode or 42
    return self.returncode

  def kill(self):
    self.returncode = -1
    self.stdin.raiseOnUse()

class MockPopen( object ):
  def __init__( self, returncode=None, stdout=None, stderr=None ):
    self._returncode = returncode
    self._stdout = stdout
    self._stderr = stderr
    self.cmd = None
    self.executable = None

  def __call__( self, cmd, executable = None, stdout=None, stderr=None, stdin=None, shell=None ):
    self.cmd = cmd
    self.executable = executable
    return MockSubprocess( self._returncode, self._stdout, self._stderr )
