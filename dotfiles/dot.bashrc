# -*- mode: sh -*-
# ----------------------------------------------------
# Bash config file
#


# ----------------------------------------------------
# Load in configuration which is common to bash and zsh
#

if [ -r ~/.bashzsh ]
then
  source ~/.bashzsh
fi

# ----------------------------------------------------
# PATH

add_to_path_front() {
    newpath=$*
    newpath=`~/bin/rmdups -F : -e . $newpath:$PATH`
    if [[ $? -eq 0 ]]
    then
        PATH=$newpath
        export PATH
    fi
}

add_to_path_end() {
    add_to_path_front $PATH:$*
}

add_to_path_front $HOME/bin
add_to_path_end   /cygdrive/c/Program\ Files/Java/jdk1.6.0_21/bin
add_to_path_end   /cygdrive/c/Ruby193/bin

# ----------------------------------------------------
# aliases
alias      sa='unalias -a; . ~/.bashrc'

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

go() {
    file=$*
    if [[ ! -e $file ]]
    then
        file=`which $file`
    elif [[ -L $file ]]
    then
        file=`readlink $file`
    fi

    if [[ -d $file ]]
    then
        cd $file
    elif [[ -e $file ]]
    then
        dir=`dirname $file`
        cd $dir
    fi
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
complete -c lw where type which python27 winpath cygpath

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
    # http://linuxgazette.net/issue65/padala.html
    #
    # <ESC>[{attr};{fg};{bg}m
    #
    # {attr} is one of
    # 0  Normal (default).
    # 1  Bold.
    # 2  Dim
    # 3  Underline
    # 4  Underlined.
    # 5  Blink (appears as Bold).
    # 7  Inverse.
    # 8  Invisible, i.e., hidden (VT300).
    #
    # {fg} (foreground color) is one of
    # 30 Black.
    # 31 Red.
    # 32 Green.
    # 33 Yellow.
    # 34 Blue.
    # 35 Magenta.
    # 36 Cyan.
    # 37 White.
    # 39 default (original).
    #
    # {bg} (background color) is one of:
    # 40 Black.
    # 41 Red.
    # 42 Green.
    # 43 Yellow.
    # 44 Blue.
    # 45 Magenta.
    # 46 Cyan.
    # 47 White.
    # 49 default (original).

    function format_prompt
    {
        local prev_exit_status=$?

        local line_color='\[\e[1;33m\e[44m\]' # Bold Yellow on Blue
        local path_color='\[\e[32m\]'         # Green
        local fail_color='\[\e[1;31m\e[44m\]' # Bold Red on Blue
        local time_color='\[\e[36m\]'         # Cyan
        local reset_color='\[\e[0m\]'

        # If we are on an unexpected machine, change the prompt to a
        # Red background
        #
        #if [[ ! `hostname` =~ ^(casqa|invest|vnc) ]]
        #then
        #    line_color='\[\e[1;33m\e[41m\]' # Bold Yellow on Blue
        #    fail_color='\[\e[1;34m\e[41m\]' # Bold Red on Blue
        #fi

        if [[ $prev_exit_status -ne 0 ]]
        then
            line_color=$fail_color
        fi

        local newPWD
        if false
        then
            local pwdmaxlen=130
            if [ $HOME == "$PWD" ]
            then
                newPWD="~"
            elif [ $HOME == ${PWD:0:${#HOME}} ]
            then
                newPWD="~${PWD:${#HOME}}"
            else
                newPWD=$PWD
            fi
            if [ ${#newPWD} -gt $pwdmaxlen ]
            then
                # .../last/three/dirs
                tmp="${PWD%/*/*/*}";
                if [ ${#tmp} -gt 0 -a "$tmp" != "$PWD" ]
                then
                    newPWD=".../${PWD:${#tmp}+1}"
                else
                    newPWD="+/\\W"
                fi
            fi
        else
            newPWD=$PWD
        fi

        local stop=$SECONDS
        local start=${PREEXEC_TIME:-$stop}
        let elapsed=$(($stop-$start))
        if [ $elapsed -gt 3600 ]
        then
            local etime=$(printf "%02dh %02dm %02ds" $((elapsed/3600)) $((elapsed/60%60)) $((elapsed%60)))
        elif [ $elapsed -gt 60 ]
        then
            local etime=$(printf "%02dm %02ds" $((elapsed/60%60)) $((elapsed%60)))
        else
            local etime=$(printf "%02ds" $elapsed)
        fi

        local title=""
        export EXTRA_TITLE
        : ${EXTRA_TITLE:=""}
        if isscreen
        then
            # This what we'd set title to if we wanted screen to do the work of
            # adding the currently running command
            #   title='\[\033k\033\134\]'
            # But we handle it ourselves with this function:
            set_default_screen_title
        else
            # This version also shows the username:
            #title='\[\033]0;\u@\h:\w\007\]'
            title='\[\033]0;${EXTRA_TITLE}\h:\w\007\]'
        fi

        PS1="${title}${line_color}\\! ${time_color}[$etime][\\t]${path_color}[\\h:${newPWD}]${reset_color}\n\$ "
    }

    #
    # Sets the EXTRA_TITLE variable, which will show up as part of the
    # window's title bar (by way of the prompt)
    #
    function settitle
    {
        if [ "$#" -ne 0 ]; then
            EXTRA_TITLE="($*):"
        else
            EXTRA_TITLE=$*
        fi
    }

    #
    # Returns true iff we are in a GNU screen instance
    #
    function isscreen
    {
      [ "$TERM" == 'screen-bce' ]
    }

    #
    # Sets the current tab's title in gnu screen.  If the argument is the
    # empty string, we use the name of the shell (defaults to bash)
    #
    function set_screen_title
    {
        local newtitle=$1
        if [ "$newtitle" == "" ]
        then
            newtitle=${SHELL:-bash}
        fi
        /bin/echo -ne "\ek${newtitle}\e\\"
    }

    #
    # Sets the current tab's title to the default value, which includes
    # the currently running command and the name of the citc client
    #
    function set_default_screen_title
    {
       set_screen_title "${EXTRA_TITLE}${CMD_FOR_SCREEN_TITLE}"
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
                    if isscreen
                    then
                        # Take the current command, remove arguments, and take the basename
                        export CMD_FOR_SCREEN_TITLE=`echo $BASH_COMMAND | cut -d " " -f 1 | xargs basename`
                        set_default_screen_title
                        export CMD_FOR_SCREEN_TITLE=""
                    fi
                }
                # no precmd for now: we do everything we need in format_prompt
                preexec_install
            else
                echo "WARNING: Could not find preexec.bash" >/dev/stderr
            fi
            ;;
        *) # not interactive: do not mess with complicated prompts
            ;;
    esac
fi
