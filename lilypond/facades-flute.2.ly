%{

Facades
Flute Part

this was an attempt to put the difference voices in the same bar next
to each other, but it didn't work.  

%}

\version "2.14.1"
%\include "english.ly"
#(set-default-paper-size "letter")

\header {
  title = "No. 5 Facades"
  subtitle = "from Glassworks"
  composer = "Philip Glass"
  piece = "Flute 1 & 2 (Transcribed from the Soprano Sax part)"
}

\layout {
  \context {
    \Staff \RemoveEmptyStaves
  }
}

intro = \relative c'' {
  << { r1. | r | } 
     { r1. | r | } >>
}

% can't say repetition12, I guess you can't have numbers in variable
% names.
repetitionAB = \relative c'' {
  \mark \default
  << {
    e | e |
    \repeat volta 2 {
      r2. f~| f~ f4 f-_ f-_ |
      e1.~ | e2. r |
    }
    \repeat volta 2 {
      r d~ | d4. r d2. |
      e1.~ | e2. r|
    }
    r2. r4. d~ | d2.~ d4 d d |
    \once \override Score.RehearsalMark #'break-visibility = #end-of-line-visible
    \once \override Score.RehearsalMark #'self-alignment-X = #RIGHT
    \mark "D.C."
    \break
    % Page 2 (50)
    c2.~ c4. c4.~ | c2. r |
  } {
    \repeat unfold 2 { r }
    \repeat volta 2 { \repeat unfold 4 { r } }
    \repeat volta 2 { \repeat unfold 4 { r } }
    \repeat unfold 4 { r }
  } >>
}

repetitionD = \relative c'' {
  \mark \default
  << {
    c8(  a c) e( dis e) c( a  c) e( dis e) |
  } {
    e,8( c e) a( e   a) e( c  e) a( c   a) |
  } >>
  << {
    c(  a c) e( dis e) c  a( b  c  d   e) |
  } {
    e(  c e) a( e   a) e  a( b  c  b   a) |
  } >>
  \repeat volta 2 {
    << {
      c( aes c) e( d   e) c( aes  c)  e( d   e)   |
    } {
      f( c f) aes( f aes) f( c    f)  aes( f   aes) |
    } >>
    << {
      c( aes c) e( d   e) c  aes( bes c  d   ees) |
    } { 
      f( c f) aes( f aes) f  aes( bes c    bes aes) |
    } >>
    << {
      c( a   c) e( dis e) c( a    c)  e( dis e)   |
    } { 
      e( c e) a( e a) e( c  e) a( c a) |
    } >>
    << {
      c( a   c) e( dis e) c  a(   b   c  d   e)   |
    } {
      e( c e) a( e a) e  a( b  c  b a) |
    } >>
  }
}

\score {
  \clef treble
  \time 12/8
  \tempo 4=89

  \intro
    
  \repetitionAB
    
  \repetitionD

}


