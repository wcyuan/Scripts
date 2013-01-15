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
alias ipython='python ~/usr/pkgs/ipython-0.12/ipython.py'

alias     pgm='cd ~/code/local/octave/pgmclass/pa9/'

gitall() {
    for d in ~/code/classes ~/code/github/* ~/code/local ~/code/saas-class-hw3
    do
      if [ -d $d ]
      then
          echo " -- $d"
          (cd $d ; git status -s)
      fi
    done
}

saas() {
    # e.g. ec2-23-22-197-139.compute-1.amazonaws.com
    host=$1
    ssh -L *:3000:localhost:3000 -i ~/code/classes/saas/AWSEC2.pem ubuntu@$host
}

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
# Should use ack instead?
alias   findgrep='find . -name .svn -prune -o -type f  -print0 | xargs -0 grep -H --color'

# find
alias   findtext='find . -name .svn -prune -o -type f -print'
alias   findpath='find . $path -type f'
findname() {
    pattern="$*"
    find . -iname "*$pattern*" | grep -i "$pattern"
}

# rarely used
alias   ruinterm="echo -n ^N"
alias    fixterm="echo -n "
alias        hex='printf "%x\n"'
alias       beep='perl -e "print \"\a\";"'
alias        fep=rlwrap

embolden() {
    # Takes one argument, which is a pattern.
    #
    # Passes through stdin, but highlights the pattern in bold red.
    #
    # terminal colors are specified as "1;31"
    # 1 means bold
    # 31 means red
    sed "s/\($1\)/[1;31m\1[m/g"
}

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

# See
# http://clalance.blogspot.com/2011/10/git-bash-prompts-and-tab-completion.html
# and http://repo.or.cz/w/git.git/blob/HEAD:/contrib/completion/git-completion.bash
# or https://github.com/git/git/tree/master/contrib/completion
# for git completion files
if [ -f "$HOME/.git-completion.sh" ]; then
    . $HOME/.git-completion.sh
fi
if [ -f "$HOME/.git-prompt.sh" ]; then
    . $HOME/.git-prompt.sh
fi

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

# turn off cygwin xemacs warning
nodosfilewarning=1
export nodosfilewarning

# ----------------------------------------------------

# ssa
#
# ssh-agent code from
# http://help.github.com/ssh-key-passphrases/
#
# This stores the pid of the ssh-agent in a file, so I assume it
# doesn't work if .ssh is an NFS directory shared by multiple machines
# (because the file will exist on many machines, but will only contain
# the pid of one ssh-agent running on one of those machiens)
#
SSH_ENV="$HOME/.ssh/environment"

# start the ssh-agent
function start_agent {
    echo "Initializing new SSH agent..."
    # spawn ssh-agent
    if [ -f "$SSH_ENV" ]; then
        rm -f $SSH_ENV
    fi
    ssh-agent | sed 's/^echo/#echo/' > "$SSH_ENV"
    echo succeeded
    chmod 600 "$SSH_ENV"
    . "$SSH_ENV" > /dev/null
    ssh-add
}

# test for identities
function test_identities {
    # test whether standard identities have been added to the agent already
    idents=`ssh-add -l 2>&1`
    if [ $? -ne 0 ]; then
        # We get here if the agent isn't running.  It would say
        # Could not open a connection to your authentication agent.
        start_agent
    else
        echo $idents | grep "The agent has no identities" > /dev/null
        if [ $? -eq 0 ]; then
            ssh-add
            # $SSH_AUTH_SOCK broken so we start a new proper agent
            if [ $? -eq 2 ];then
                start_agent
            fi
        fi
    fi
}

# check for running ssh-agent with proper $SSH_AGENT_PID
if [ -n "$SSH_AGENT_PID" ]; then
    ps -ef | grep "$SSH_AGENT_PID" | grep ssh-agent > /dev/null
    if [ $? -eq 0 ]; then
	test_identities
    fi
# if $SSH_AGENT_PID is not properly set, we might be able to load one from
# $SSH_ENV
else
    if [ -f "$SSH_ENV" ]; then
	. "$SSH_ENV" > /dev/null
    fi
    ps -ef | grep "$SSH_AGENT_PID" | grep -v grep | grep ssh-agent > /dev/null
    if [ $? -eq 0 ]; then
        test_identities
    else
        # Don't start_agent until we need it.  Otherwise, it will ask
        # for your passphrase every time we start a new shell.
        #
        #start_agent
        #
        :
    fi
fi

# ----------------------------------------------------

if false
then

    # Ansi terminal color codes
    #    Foreground Colours
    #    30	Black
    #    31	Red
    #    32	Green
    #    33	Yellow
    #    34	Blue
    #    35	Magenta
    #    36	Cyan
    #    37	White
    #
    #    Background Colours
    #    40	Black
    #    41	Red
    #    42	Green
    #    43	Yellow
    #    44	Blue
    #    45	Magenta
    #    46	Cyan
    #    47	White

    function format_prompt
    {
        local PREV_EXIT_STATUS=$?

        local LINE_COLOR='\[\e[1;33m\e[44m\]' # Bold Yellow on Blue
        local PATH_COLOR='\[\e[32m\]'         # Green
        local FAIL_COLOR='\[\e[1;31m\e[44m\]' # Bold Red on Blue
        local TIME_COLOR='\[\e[36m\]'         # Cyan
        local RESET_COLOR='\[\e[0m\]'

        if [[ $PREV_EXIT_STATUS -ne 0 ]]
        then
            LINE_COLOR=$FAIL_COLOR
        fi

        #local pwdmaxlen=30
        #if [ $HOME == "$PWD" ]
        #then
        #    newPWD="~"
        #elif [ $HOME == ${PWD:0:${#HOME}} ]
        #then
        #    newPWD="~${PWD:${#HOME}}"
        #else
        #    newPWD=$PWD
        #fi
        #if [ ${#newPWD} -gt $pwdmaxlen ]
        #then
        #    # .../last/three/dirs
        #    tmp="${PWD%/*/*/*}";
        #    if [ ${#tmp} -gt 0 -a "$tmp" != "$PWD" ]
        #    then
        #        newPWD=".../${PWD:${#tmp}+1}"
        #    else
        #        newPWD="+/\\W"
        #    fi
        #fi

        stop=$SECONDS
        start=${PREEXEC_TIME:-$stop}
        let elapsed=$(($stop-$start))
        if [ $elapsed -gt 3600 ]
        then
            ETIME=$(printf "%02dh %02dm %02ds" $((elapsed/3600)) $((elapsed/60%60)) $((elapsed%60)))
        elif [ $elapsed -gt 60 ]
        then
            ETIME=$(printf "%02dm %02ds" $((elapsed/60%60)) $((elapsed%60)))
        else
            ETIME=$(printf "%02ds" $elapsed)
        fi

        # This version also shows the username:
        #TITLE='\[\033]0;\u@\h:\w\007\]'
        TITLE='\[\033]0;\h:\w\007\]'
        PS1="${TITLE}${LINE_COLOR}\\! ${TIME_COLOR}[$ETIME][\\t]${PATH_COLOR}[\\h:${PWD}]${RESET_COLOR}\n$ "
    }

    PROMPT_COMMAND='format_prompt'
    # Detecting whether in interactive mode:
    #     http://www.gnu.org/software/bash/manual/html_node/Is-this-Shell-Interactive_003f.html
    case "$-" in
        *i*)
            # get preexec.bash from http://www.twistedmatrix.com/users/glyph/preexec.bash.txt
            if [ -f preexec.bash ]
            then
                . preexec.bash
                # called before each command and starts stopwatch
                function preexec () {
                    export PREEXEC_CMD="$BASH_COMMAND"
                    export PREEXEC_TIME=$SECONDS
                }
                # no precmd for now: we do everything we need in format_prompt
                preexec_install
            fi
            ;;
        *) # not interactive: do not mess with complicated prompts
            ;;
    esac
fi
