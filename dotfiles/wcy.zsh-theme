# -*- mode: sh -*-
#
# Starts from robbyrussell.zsh-theme and adds the time and how long the last command took.
#

function setprompt() {
  if [ $timer ]; then
    timer_show=$(($SECONDS - $timer))
    timer_show="${timer_show}s|"
  fi

  # http://zsh.sourceforge.net/Doc/Release/Prompt-Expansion.html
  # Some prompt variables:
  #
  # %c == last part of the current directory
  # %~ == full current directory, with ~
  # %d == full current directory, with no ~
  # To have a newline in your path, just put an actual newline in the
  # variable (\n doesn't work)
  ret_status="%(?:%{$fg_bold[green]%}:%{$fg_bold[red]%} %s)[${timer_show}%D{%l:%M:%S%P}]"
  export PROMPT='${ret_status}%{$fg_bold[green]%}%p %{$fg[cyan]%}%~ %{$fg_bold[blue]%}$(git_prompt_info)%{$fg_bold[blue]%} % %{$reset_color%}
$ '
}

setprompt

ZSH_THEME_GIT_PROMPT_PREFIX="git:(%{$fg[red]%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_DIRTY="%{$fg[blue]%}) %{$fg[yellow]%}✗%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_CLEAN="%{$fg[blue]%})"

#
# Add command runtime
# from https://coderwall.com/p/kmchbw/zsh-display-commands-runtime-in-prompt
#
function preexec() {
  timer=${timer:-$SECONDS}
}

function precmd() {
  if [ $timer ]; then
    setprompt
    unset timer
  fi
}
