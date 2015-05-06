#!/usr/bin/env python
"""Install dotfiles.

I like to keep dotfiles under version control.  That means the
dotfiles in my home directory should be symlinks to the files in
version control.  This script creates those symlinks.  This makes it
easy to repoint my installed dotfiles to the files in different
checkouts.
"""

# --------------------------------------------------------------------

import optparse
import os

# --------------------------------------------------------------------

#
# Each file is a tuple of 1 or 2 elements.
#
# If the tuple has 2 elements, the first element is the link to
# create, the second is the name of the file to link to.
#
# If the tuple has 1 element, then it's the name of the link to
# create.  We assume that the link will point to a file of the same
# name except with "dot" added to the front of it.
#
FILES = (
    ('.bashrc',),
    ('.bash_profile',),
    ('.bashzsh',),
    ('.emacs',),
    ('.gitconfig',),
    ('.preexec.bash',),
    ('.screenrc',),
    ('.toprc',),
    ('.tmux.conf',),
    ('.zshrc',),
    ('~/.local/share/applications/emacsclient.desktop', 'emacsclient.desktop'),
    )

# By default, we link to files in the directory where this script
# lives.
DEFAULT_TGTDIR = os.path.dirname(os.path.realpath(__file__))

# By default, we link from the user's home directory
DEFAULT_LINKDIR = os.path.expanduser("~")

# --------------------------------------------------------------------

def main():
  opts, args = getopts()

  if len(args) > 0:
    files = args
  else:
    files = FILES

  for filenames in files:
    (fn, tgt) = resolve_files(filenames, tgtdir=opts.dotdir, linkdir=opts.dir)
    update_file(fn, tgt, no_write=opts.no_write, force=opts.force)

def getopts():

  parser = optparse.OptionParser()

  parser.add_option("--no_write",
                    action="store_true",
                    help="Print actions without executing them")

  parser.add_option("--dotdir",
                    help="The directory containing the dotfiles to link to.  "
                    "Defaults to wherever you are running this script from",
                    default=DEFAULT_TGTDIR)

  parser.add_option("--dir",
                    help="The directory to put the links.  Defaults to your "
                    "home directory",
                    default=DEFAULT_LINKDIR)

  parser.add_option("--force",
                    help="Force overriding existing dot files")

  (opts, args) = parser.parse_args()

  return (opts, args)

# --------------------------------------------------------------------

def run(pyfunc, cmd, no_write, always=False):
  """Run a python function.

  Print what is being run.  The thing to print is not the same as the
  function.  Typically this is for running shell commands for which
  python has builtin versions.  So we print the shell command, but we
  run the python builtin version.

  Only run if no_write is False or if always is True.

  """
  if not always and no_write:
    print 'NO WRITE: Would run: {0}'.format(cmd)
  else:
    print 'RUNNING: {0}'.format(cmd)
    pyfunc()

def resolve_files(filenames, tgtdir=None, linkdir=None):
  """Figure out exactly where the link and target live.

  Resolves the tuples in FILES.  Each tuple should have one or two
  elements.  If it is one element, it is the link.  If it is two, it
  is the link and the target.

  If no target is given and link starts with ".", the target's name
  becomes "dot" + link.

  If no directory is given for the link, add the linkdir.
  If no directory is given for the target, add the tgtdir.

  """
  if len(filenames) == 2:
    (fn, tgt) = filenames
  else:
    (fn,) = filenames
    (fdir, fbase) = os.path.split(fn)
    if fbase.startswith("."):
      fbase = "dot{0}".format(fbase)
    tgt = os.path.join(fdir, fbase)

  if os.path.dirname(tgt) == '':
    tgt = os.path.join(tgtdir, tgt)

  if os.path.dirname(fn) == '':
    fn = os.path.join(linkdir, fn)

  fn = os.path.expanduser(fn)
  tgt = os.path.expanduser(tgt)

  return (fn, tgt)

def update_file(fn, tgt, no_write=False, force=False):
  """
  Roughly equivalent to:
    ln -s tgt fn
  But does nothing if fn already points to tgt
  and complains if fn exists and points somewhere else (unless force is True)
  """
  if os.path.lexists(fn):
    if os.path.islink(fn):
      existing = os.readlink(fn)
      if os.path.realpath(existing) == os.path.realpath(tgt):
        print "{0} already points to {1}".format(fn, tgt)
        return
      elif not force:
        print("{0} already exists and points to the wrong place.  "
              "({1} instead of {2}).  Use --force to overwrite.".format(
                  fn, existing, tgt))
        return
    elif not force:
      print("{0} already exists and isn't a link, not pointing to {1}.  "
            "Use --force to overwrite.".format(fn, tgt))
      return
    run(lambda: os.remove(fn), 'rm "{0}"'.format(fn), no_write=no_write)

  run(lambda: os.symlink(tgt, fn), 'ln -s "{0}" "{1}"'.format(tgt, fn),
      no_write=no_write)

# --------------------------------------------------------------------

if __name__ == '__main__':
  main()
