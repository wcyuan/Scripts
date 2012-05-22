# -*- mode: bash -*-
# ----------------------------------------------------
# PATH

PATH=$PATH:/cygdrive/c/Program\ Files/Java/jdk1.6.0_21/bin
PATH=$PATH:$HOME/bin

# ----------------------------------------------------
# aliases
alias      rm='rm -i'
alias      cp='cp -i'
alias      mv='mv -i'
alias       l='ls -lF'
alias      la='ls -alF'
alias     lsd='ls -dlF'
alias     ltr='ls -lrt'
alias      sa='unalias -a; . ~/.bashrc'
alias ipython='python ~/ipython-0.12/ipython.py'

alias     pgm='cd ~/testbed/local/octave/pgmclass/pa9/'

which() {
    args=$*
    if [ "`type -t $args`" == "file" ]
    then
        # if we were only given one argument, and it's a file, then
        # run with -p which returns the path to that file without the
        # "foo is " part
        type -p $args
    else
        type $args
    fi
}
alias      where='which -a'

# grep
alias       grep='grep --color'
alias      egrep='egrep --color'
# -H forces printing of the file name, even if there is only one file
alias      xgrep='xargs -d"\n" grep -H --color'
alias     xegrep='xargs -d"\n" egrep -H --color'
# Should use ack instead
alias   findgrep='find . -name .svn -prune -o -type f  -print0 | xargs -0 grep -H --color'

# find
alias   findtext='find . -name .svn -prune -o -type f -print'
alias   findpath='find . $path -type f'

# rarely used
alias   ruinterm="echo -n ^N"
alias    fixterm="echo -n "
alias        hex='printf "%x\n"'
alias       beep='perl -e "print \"\a\";"'

# ----------------------------------------------------
# Completion
#
# http://www.gnu.org/software/bash/manual/bashref.html#Programmable-Completion-Builtins
#
# List all completions with the command (if no word, lists all)
#   complete -p [word]
# Remove completions with the command (if no word, removes all)
#   complete -r [word]

# directories
complete -d cd chdir pushd popd mkdir rmdir

# commands
complete -c lw where type which

#----------------------------------------------------------------------

# don't clobber files
set -o noclobber

# ----------------------------------------------------

# python
PYTHONPATH=$HOME/usr/python
export PYTHONPATH

# ----------------------------------------------------

# less
# use a verbose prompt
LESS='-M'
export LESS

# ----------------------------------------------------

# ssa
#
# Runs ssa-add on startup.  This will ask for your passphrase every
# time it starts up.
#
# ssh-agent code from 
# http://help.github.com/ssh-key-passphrases/
#
SSH_ENV="$HOME/.ssh/environment"

# start the ssh-agent
function start_agent {
    echo "Initializing new SSH agent..."
    # spawn ssh-agent
    ssh-agent | sed 's/^echo/#echo/' > "$SSH_ENV"
    echo succeeded
    chmod 600 "$SSH_ENV"
    . "$SSH_ENV" > /dev/null
    ssh-add
}

# test for identities
function test_identities {
    # test whether standard identities have been added to the agent already
    ssh-add -l | grep "The agent has no identities" > /dev/null
    if [ $? -eq 0 ]; then
        ssh-add
        # $SSH_AUTH_SOCK broken so we start a new proper agent
        if [ $? -eq 2 ];then
            start_agent
        fi
    fi
}

## check for running ssh-agent with proper $SSH_AGENT_PID
#if [ -n "$SSH_AGENT_PID" ]; then
#    ps -ef | grep "$SSH_AGENT_PID" | grep ssh-agent > /dev/null
#    if [ $? -eq 0 ]; then
#	test_identities
#    fi
## if $SSH_AGENT_PID is not properly set, we might be able to load one from
## $SSH_ENV
#else
#    if [ -f "$SSH_ENV" ]; then
#	. "$SSH_ENV" > /dev/null
#    fi
#    ps -ef | grep "$SSH_AGENT_PID" | grep -v grep | grep ssh-agent > /dev/null
#    if [ $? -eq 0 ]; then
#        test_identities
#    else
#        start_agent
#    fi
#fi
