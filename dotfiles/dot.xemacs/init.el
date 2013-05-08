;; ---------------------------------------------------------------- ;;
;;
;; Emacs Cheatsheet:
;;
;; -- Essential --
;;
;;   You can't use emacs with knowing these
;;
;; C-x C-f   -- open
;; C-x C-s   -- save
;; C-x C-w   -- save-as
;; C-x C-v   -- open, replacing current file
;; C-x k     -- close (kill-buffer)
;; C-z       -- suspend/minimize
;; C-x C-c   -- quit
;; C-g       -- stop the running command
;;
;; -- Basic --
;;
;;   Things any decent editor has to be able to do.
;;
;; C-_       -- undo
;; C-x u     -- undo
;;
;; M-f       -- move forward a word
;; M-<right> -- move forward a word
;; M-b       -- move backwards a word
;; M-<left>  -- move backwards a word
;; M-<up>    -- move forward a block
;; M-<down>  -- move backwards a block
;; C-a       -- go to beginning of line
;; C-e       -- go to end of line
;; M-g g     -- goto line number (emacs)
;; M-g       -- goto line number (xemacs)
;; M-<       -- goto beginning of file
;; M->       -- goto end of file
;;
;; C-s       -- search
;; C-r       -- backwards search
;;
;; M-<backspace>
;;           -- kill (cut) previous word
;; M-d       -- kill next word
;; C-k       -- kill rest of line
;; C-y       -- yank (paste)
;; C-u C-y   -- yank, but leave the cursor where it is
;; M-y       -- replace last yank with next thing in the kill buffer
;;
;; Ins       -- switch to overwrite mode
;;
;; -- Medium --
;;
;;   Some of the things that make emacs cool
;;
;; M-x       -- run a command
;;
;; C-x 2     -- split frame horizontally
;; C-x 3     -- split frame vertically
;; C-x o     -- switch between frames
;; C-x 1     -- get rid of all frames but this one
;; C-x 0     -- get rid of this frame
;; C-x 5 2   -- open a new window
;; C-x 5 o   -- switch between windows
;; C-x 5 1   -- close all windows but this one
;; C-x 5 0   -- close this window
;;
;; C-space   -- begin marking a region.  Also just shift-<arrow>
;; C-w       -- kill-region
;; M-w       -- copy-region
;; C-x C-x   -- move cursor to the mark
;;
;; C-t       -- switch this letter with the previous letter
;; M-t       -- switch this word with the previous word
;;
;; M-u       -- make the next word all caps
;; M-l       -- make the next word all lowercase
;; M-c       -- make the next word title (first letter capital, rest lower)
;;
;; M-space   -- collapse whitespace into a single space
;;
;; -- Advanced --
;;
;;   You only need these occasionally, but when you do, they are awesome
;;
;; C-u <n> <cmd>
;;           -- repeat command <cmd> <n> times.  <n> defaults to 4
;; C-u is a general "universal argument" that is used to alter the
;; behavior of many emacs commands.
;;
;; C-x (     -- start defining a macro
;; C-x )     -- finish defining a macro
;; C-x e     -- execute the last defined macro
;;
;; C-r k     -- kill rectangle
;; C-r y     -- yank rectangle
;;
;; M-C-%     -- query-replace-string
;;
;; M-q       -- re-justify block
;; C-M-\     -- re-tabify a block
;; M-;       -- comment or uncomment out a region
;;
;; C-x n n   -- narrow to region.  This only shows this portion of the
;;              buffer and makes the rest inaccessible.
;; C-x n w   -- Widen.  Un-narrow, so you can see thw whole buffer again
;;
;; M-!       -- Run a shell command
;;
;; M-x make-frame-on-display
;;           -- open a window on a different display
;;
;; M-x describe-function
;;           -- describe a function and say what key sequence it is bound to
;;
;; M-x describe-key
;;           -- say what function a key sequence is bound to
;;
;; Dynamic Abbrev Expansion:
;; M-/       -- Search the buffer for possible completions
;; C-M-/     -- Show all possible completions
;;
;; http://www.gnu.org/software/emacs/manual/html_node/emacs/index.html
;; http://www.emacswiki.org/emacs/EmacsWiki
;;
;; ---------------------------------------------------------------- ;;
;;
;; When definine new key bindings, consider the emacs key binding
;; conventions:
;;
;; http://www.gnu.org/software/emacs/manual/html_node/elisp/Key-Binding-Conventions.html#Key-Binding-Conventions
;;
;; \C-c-letter is reserved for users
;; <F5>-<F9> are reserved for users
;; \C-c-non-letter is reserved for major or minor modes
;; Don't bind \C-h (help), \C-g (exit); don't end with <ESC>
;; Careful when binding \C-u
;;
;; ---------------------------------------------------------------- ;;
;;
;; system-wide emacs lisp files typically live at /usr/share/{x,}emacs
;;
;; ---------------------------------------------------------------- ;;


;; ---------------------------------------------------------------- ;;
;; Macros for determining whether we are in emacs or xemacs, etc.
;;
(defmacro GNUEmacs (&rest x)
  (list 'if (string-match "GNU Emacs" (version)) (cons 'progn x)))
(defmacro XEmacs (&rest x)
  (list 'if (string-match "XEmacs" (version)) (cons 'progn x)))
(defun emacs-number ()
  "Return emacs version as a number"
  (interactive)
  (+ emacs-major-version (/ emacs-minor-version 10.0)))
(defmacro Unix (&rest x)
  (list 'if (not (eq system-type 'windows-nt)) (cons 'progn x)))
(defmacro Windows (&rest x)
  (list 'if (eq system-type 'windows-nt) (cons 'progn x)))

;; ---------------------------------------------------------------- ;;
;; Various configuration
;;
(setq frame-title-format mode-line-buffer-identification)
(setq enable-local-variables t)         ;; Let files specify major-mode
(setq-default indent-tabs-mode nil)     ;; Indent with spaces, not tabs
(setq inhibit-startup-message t)        ;; No emacs start-up message
(setq dired-listing-switches (concat dired-listing-switches "F"))
(put 'narrow-to-region 'disabled nil)   ;; Enable C-x-n-n
(setq diff-switches "-wu")              ;; Switches to pass to diff
(setq require-final-newline t)          ;; Always make sure files end
                                        ;; with newlines

;; customize mode line
(setq display-time-string-forms '((format "%s:%s%s" 12-hours minutes am-pm)))
(display-time)                          ;; Show current time

;; ---------------------------------------------------------------- ;;
;; Turn off the toolbar
;;
(if (featurep 'toolbar)                 ;; XEmacs
    (set-specifier default-toolbar-visible-p nil)) ;; turn off toolbar
(if (functionp 'tool-bar-mode)          ;; GNUEmacs 21.3
    (tool-bar-mode -1))                 ;; turn off toolbar

;; ---------------------------------------------------------------- ;;
;; Make C-xC-c kill this frame before killing all of emacs
;;
;; Otherwise, if you just want to kill a frame, use C-x 5 0
;;
(global-set-key "\C-x\C-c" 'close-frame-or-exit)
(defun close-frame-or-exit ()
  "If multiple frames, close a frame, otherwise exit emacs."
  (interactive)
  (if (= (length (frame-list)) 1)
      (save-buffers-kill-emacs)
    (delete-frame)))

;; ---------------------------------------------------------------- ;;
;; Bash mode
;;
(defun bash-mode ()
  "Major mode for editing bash shell scripts.
Enters shell-script[bash] mode (see `shell-script-mode')."
  (interactive)
  (sh-mode)
  (sh-set-shell "bash"))

(defun tcsh-mode ()
  "Major mode for editing tcsh shell scripts.
Enters shell-script[tcsh] mode (see `shell-script-mode')."
  (interactive)
  (sh-mode)
  (sh-set-shell "tcsh"))

;; use bash-mode for .bashrc
(setq auto-mode-alist (append '(("\\.bashrc\\'" . bash-mode)
                                )
                              auto-mode-alist))

;; ---------------------------------------------------------------- ;;
;; Perl
;;

; Prefer cperl-mode to perl-mode.
;
; http://www.emacswiki.org/emacs/CPerlMode
;; cperl-mode is preferred to perl-mode
;; "Brevity is the soul of wit" <foo at acm.org>
;
; One way to do this is to alias perl-mode to cperl-mode
(defalias 'perl-mode 'cperl-mode)

; the defalias doesn't always seem to work, so try these too.
(fset 'perl-mode 'cperl-mode)

; In case the aliases don't work, we can also change the
; auto-mode-alist
(mapc
 (lambda (pair)
   (if (eq (cdr pair) 'perl-mode)
       (setcdr pair 'cperl-mode)))
 (append auto-mode-alist interpreter-mode-alist))

;
; Example of cperl-continued-statement-offset
; value of 0:
;
;   if (one() &&
;       two())
;   {
;       my $a = 'abc' .
;       'def';
;   }
;   print
;   one(),
;   two();
;   dothis()
;   or die();
;
; value of 4:
;
;   if (one() &&
;           two())
;       {
;           my $a = 'abc' .
;               'def';
;       }
;   dothis()
;       or die();
;   print
;       one(),
;           two();
;
; This is annoying.  I want an offset of 4 for things like "a or
; die()" and for "print one()" but an offset of 0 for open braces on
; new lines.  I want an offset on the first line continuation after a
; print, but not the second continuation line.
;
; For now, I'll probably choose an offset of 0.
;

;
; Example of cperl-close-paren-offset
; value of 0:
;
;   unless ($a
;           )
;   unless (
;       $a
;       )
;
; value of -4:
;
;   unless ($a
;       )
;   unless (
;       $a
;   )
;
;

;
; Examples of cperl-indent-parens-as-block and cperl-close-paren-offset,
; All with cperl-close-paren-offset=0

; cperl-indent-parens-as-block t, cperl-close-paren-offset 0
;
;    $foo = {
;        $a
;        };
;    $foo = { $a
;             };
;    $foo = {$a
;            };
;    $foo =
;    {
;        $a
;        };
;    unless (
;        $a
;        ) {
;    }
;    unless ( $a
;             ) {
;    }
;    unless ($a
;            ) {
;    }
;    unless (
;        $a
;        )
;    {
;    }
;    unless ( $a
;             )
;    {
;    }
;    unless ($a
;            )
;    {
;    }
;    function_call(
;        $arg1,
;        $arg2,
;        another_function_call(
;            $arg3

; cperl-indent-parens-as-block t, cperl-close-paren-offset -4
; (this one looks the best to me)
;
;    $foo = {
;        $a
;    };
;    $foo = { $a
;         };
;    $foo = {$a
;        };
;    $foo =
;    {
;        $a
;    };
;    unless (
;        $a
;    ) {
;    }
;    unless ( $a
;         ) {
;    }
;    unless ($a
;        ) {
;    }
;    unless (
;        $a
;    )
;    {
;    }
;    unless ( $a
;         )
;    {
;    }
;    unless ($a
;        )
;    {
;    }
;    function_call(
;        $arg1,
;        $arg2,
;        another_function_call(
;            $arg3

; cperl-indent-parens-as-block nil, cperl-close-paren-offset 0
;
;    $foo = {
;            $a
;            };
;    $foo = { $a
;            };
;    $foo = {$a
;            };
;    $foo =
;    {
;        $a
;        };
;    unless (
;        $a
;        ) {
;    }
;    unless ( $a
;             ) {
;    }
;    unless ($a
;            ) {
;    }
;    unless (
;        $a
;        )
;    {
;    }
;    unless ( $a
;             )
;    {
;    }
;    unless ($a
;            )
;    {
;    }
;    function_call(
;                  $arg1,
;                  $arg2,
;                  another_function_call(
;                                        $arg3

; cperl-indent-parens-as-block nil, cperl-close-paren-offset -4
;    $foo = {
;            $a
;        };
;    $foo = { $a
;        };
;    $foo = {$a
;        };
;    $foo =
;    {
;     $a
; };
;    unless (
;            $a
;        ) {
;    }
;    unless ( $a
;        ) {
;    }
;    unless ($a
;        ) {
;    }
;    unless (
;            $a
;        )
;    {
;    }
;    unless ( $a
;        )
;    {
;    }
;    unless ($a
;        )
;    {
;    }
;    function_call(
;                  $arg1,
;                  $arg2,
;                  another_function_call(
;                                        $arg3

; http://www.emacswiki.org/emacs/IndentingPerl
(setq cperl-indent-level 4
      cperl-continued-statement-offset 0
      cperl-close-paren-offset -4
      cperl-indent-parens-as-block t
      ;cperl-tab-always-indent t
      )

;; ---------------------------------------------------------------- ;;
;; Ruby
;;

(add-hook 'ruby-mode-hook
          (lambda()
            (GNUEmacs
             (add-hook 'local-write-file-hooks
                       '(lambda()
                          (save-excursion
                            (untabify (point-min) (point-max))
                            (delete-trailing-whitespace)
                            ))))
            (set (make-local-variable 'indent-tabs-mode) 'nil)
            (set (make-local-variable 'tab-width) 2)
            (imenu-add-to-menubar "IMENU")
            (define-key ruby-mode-map "\C-m" 'newline-and-indent)
            ;; I don't know whose idea it was to bind Meta-Backspace to
            ;; "ruby-mark-defun" in ruby-mode, but I really need it to be
            ;; backwards-kill-word.
            (define-key ruby-mode-map (kbd "M-BS") 'backward-kill-word)
            ))

;; ---------------------------------------------------------------- ;;
;; VC
;;

;;
;; C-x v v    -- check in/out
;; C-x v =    -- diff to last version
;; C-x v u    -- discard this version and checkout last committed version
;; C-x v g    -- annotate
;;
(require 'vc)

;; ---------------------------------------------------------------- ;;
;; Backups and auto-saves
;;
;; from http://snarfed.org/gnu_emacs_backup_files
;;
;; http://www.gnu.org/software/emacs/manual/html_node/emacs/Auto-Save.html#Auto-Save
;; http://www.gnu.org/software/emacs/manual/html_node/emacs/Backup.html#Backup
;;
;; Auto-save: emacs automatically saves the buffer periodically, every
;; 300 (auto-save-interval) characters or auto-save-timeout seconds.
;; It also auto-saves every time there is a fatal error.  Force an
;; auto-save with do-auto-save.  Whether you auto-save is controled by
;; auto-save-default.
;;
;; Backups: The first time you save a file, the previous version of
;; that file is saved as a backup.  After that, the backup doesn't
;; change, no matter how many times you save it, until you revisit the
;; file.  There are no backups for files controlled by version
;; control.  Whether you have backups is controled by
;; make-backup-files (or vc-make-backup-files, for version controlled
;; files).
;;

(GNUEmacs
 ;; Put autosave files (ie #foo#) and backup files (ie foo~) in ~/.emacs.d/.
 (custom-set-variables
  '(auto-save-file-name-transforms '((".*" "~/.emacs.d/autosaves/\\1" t)))
  '(backup-directory-alist '((".*" . "~/.emacs.d/backups/"))))
 ;; create the autosave dir if necessary, since emacs won't.
 (make-directory "~/.emacs.d/autosaves/" t))

(XEmacs
 ;; Auto-save
 ;; Load the auto-save.el package, which lets you put all of your autosave
 ;; files in one place, instead of scattering them around the file system.
 ;; M-x recover-all-files or M-x recover-file to get them back
 (defvar temp-directory "~/.xemacs/tmp")
 (make-directory temp-directory t)

 (setq auto-save-directory (concat temp-directory "/autosave")
       auto-save-hash-directory (concat temp-directory "/autosave-hash")
       auto-save-directory-fallback "/tmp"
       auto-save-list-file-prefix (concat temp-directory "/autosave-")
       auto-save-hash-p nil
       auto-save-timeout 100
       auto-save-interval 300)
 (make-directory auto-save-directory t)
 (require 'auto-save)

 ;; Put backups in another directory.  With the directory-info
 ;; variable, you can control which files get backed up where.
 (require 'backup-dir)
 (setq bkup-backup-directory-info
       `(
         (t ,(concat temp-directory "/backups") ok-create full-path)
         ))
 (setq make-backup-files t)
 (setq backup-by-copying t)
 (setq backup-by-copying-when-mismatch t)
 (setq backup-by-copying-when-linked t)
 (setq version-control t)
 (setq-default delete-old-versions t))

;; ---------------------------------------------------------------- ;;
;; Parens
;;
(GNUEmacs (show-paren-mode 1)                   ;; highlight matching parens
          (setq show-paren-style 'expression))  ;; highlight entire expression

; sexp mode will highlight the entire block contained in the parens,
; when the cursor is placed right after a paren
(XEmacs (require 'paren)                        ;; XEmacs
        (paren-set-mode 'sexp))                 ;; highlight entire expression

; From http://www.emacswiki.org/emacs/ParenthesisMatching#toc6
(defun goto-match-paren (arg)
  "Go to the matching parenthesis if on parenthesis.
   vi style of % jumping to matching brace."
  (interactive "p")
  (message "%s" last-command)
  (cond ((looking-at "\\s\(") (forward-list 1) (backward-char 1))
        ((looking-at "\\s\)") (forward-char 1) (backward-list 1))
        (t (self-insert-command (or arg 1)))))

(global-set-key "%" 'goto-match-paren)

;; ---------------------------------------------------------------- ;;
;; Trailing whitespace
;;
;;   only works in emacs, not xemacs
;;
;; command to remove all trailing whitespace from a file:
;;   perl -i -pne 's/\s+$/\n/' <file>
;;

;; Highlight trailing whitespace by default
(setq-default show-trailing-whitespace t)

(defun toggle-trailing-whitespace ()
  "Toggle the trailing whitespace indicator"
  (interactive)
  (if show-trailing-whitespace
      (progn
        (message "show-trailing-whitespace OFF")
        (setq show-trailing-whitespace nil))
      (progn
        (message "show-trailing-whitespace ON")
        (setq show-trailing-whitespace t)))
  (redraw-display))
(global-set-key "\C-cw" 'toggle-trailing-whitespace)

; Only works in emacs, not xemacs, because there is no
; delete-trailing-whitespace in xemacs.
(defun untabify-and-delete-trailing-whitespace ()
  "untabify and delete trailing whitespace"
  (interactive)
  (message "Removing tabs and trailing whitespace")
  (untabify (point-min) (point-max))
  (delete-trailing-whitespace)
  )
(global-set-key "\C-ct" 'untabify-and-delete-trailing-whitespace)

;; ---------------------------------------------------------------- ;;
;; Flymake (only works for emacs, not xemacs)
;;
;; http://www.gnu.org/software/emacs/manual/html_mono/flymake.html
;; http://www.emacswiki.org/emacs/PythonMode#toc8
;;

; Put flymake temp files into a common local directory so they don't
; clutter the directory the file is in.  This allows flymake to work
; on directories where you don't have permission to write.  It also
; reduces clutter from left over flymake files.
(defun flymake-create-temp-local-temp-dir (file-name prefix)
  (unless (stringp file-name)
    (error "Invalid file-name"))
  (or prefix
      (setq prefix "flymake"))
  (let* ((temp-name   (concat "~/.emacs.d/flymake-py/"
                              (file-name-nondirectory file-name)
                              "_" prefix
                              (and (file-name-extension file-name)
                                   (concat "." (file-name-extension file-name))))))
    (flymake-log 3 "create-temp-inplace: file=%s temp=%s" file-name temp-name)
    temp-name))

(when (load "flymake" t)
  (defun flymake-pylint-init ()
    (let* ((temp-file (flymake-init-create-temp-buffer-copy
                       'flymake-create-temp-local-temp-dir))
           (local-file (file-relative-name
                        temp-file
                        (file-name-directory buffer-file-name))))
      (list "epylint" (list temp-file))))

  (add-to-list 'flymake-allowed-file-name-masks
               '("\\.py\\'" flymake-pylint-init)))

(GNUEmacs
 (setq flymake-allowed-file-name-masks
       '(("\\.py\\'" flymake-pylint-init)
         ("\\.html?\\'" flymake-xml-init)
         ("\\.cs\\'" flymake-simple-make-init)
         ("\\.pl\\'" flymake-perl-init)
         ("[0-9]+\\.tex\\'" flymake-master-tex-init flymake-master-cleanup)
         ("\\.tex\\'" flymake-simple-tex-init)
         ("\\.idl\\'" flymake-simple-make-init)))
  ; remove the c, java, and xml flymake hooks since those don't seem to work.
  ;("\\.c\\'" flymake-simple-make-init)
  ;("\\.cpp\\'" flymake-simple-make-init)
  ;("\\.xml\\'" flymake-xml-init)
  ;("\\.h\\'" flymake-master-make-header-init flymake-master-cleanup)
  ;("\\.java\\'" flymake-simple-make-java-init flymake-simple-java-cleanup)
 (add-hook 'find-file-hook 'flymake-find-file-hook))


;; ---------------------------------------------------------------- ;;
;; Matlab mode
;;
(if (file-exists-p "~/.xemacs/matlab-emacs/matlab-emacs/")
    (progn
      (add-to-list 'load-path "~/.xemacs/matlab-emacs/matlab-emacs/")
      (require 'matlab-load)))

;; ---------------------------------------------------------------- ;;
;; Lilypond
(if (file-exists-p "~/.elisp/lilypond/")
    (progn
      (add-to-list 'load-path "~/.elisp/lilypond/" t)
      (load-file "~/.elisp/lilypond/lilypond-init.el")))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; ---------------------------------------------------------------- ;;
;;;
;;; Tags
;;;
;
; ;; M-. <tag>       -- search for a tag
; ;; C-u M-.         -- go to next instance of the tag
; ;; C-u - M-.       -- go to previous instance of the tag
; ;; M-*             -- go back to where you were before M-.
; ;; C-M-. <patt>    -- regexp tag search
; ;; M-x tags-search -- search for a regexp in all the files that have tags
; ;; M-,             -- go to next result in the tags-search
;
;(setq tags-file-name '"/u/yuanc/usr/tags/TAGS")
;(setq tags-build-completion-table t)
;(setq tags-auto-read-changed-tag-files t)
;(setq tags-always-exact t)             ;; make tags work "correctly"
;(Unix (setq tags-table-list '("/u/yuanc/usr/tags/TAGS")))
;(if (>= (emacs-number) 20.3)
;    (setq tags-revert-without-query t) ;; always revert tags tables w/o query
;  (setq revert-without-query '(".*"))) ;; always revert tags tables w/o query
;
;

;; ---------------------------------------------------------------- ;;
;;
;; Column Marker
;;
;; http://www.emacswiki.org/emacs/ColumnMarker
;;

(if (file-exists-p "~/.elisp/column-marker.el")
    (GNUEmacs
     (progn
       (load-file "~/.elisp/column-marker.el")

       (defun set-eighty-column ()
         "Highlight the 80th column"
         (interactive)
         (if column-marker-1
             (progn
               (column-marker-internal 'column-marker-1 nil)
               (message "80-column marker OFF")
               )
           (progn
             (column-marker-1 80)
             (message "80-column marker ON")
             )))
       (global-set-key "\C-ce" 'set-eighty-column)
       (add-hook 'cperl-mode-hook (lambda () (interactive) (column-marker-1 80)))
       (add-hook 'python-mode-hook (lambda () (interactive) (column-marker-1 80)))
       (add-hook 'java-mode-hook (lambda () (interactive) (column-marker-1 80)))
       (add-hook 'c-mode-hook (lambda () (interactive) (column-marker-1 80)))
       )))

;; ---------------------------------------------------------------- ;;
;; Nice unique buffer names.  More descriptive than sim.pl<2>
;;

(require 'uniquify)
(setq uniquify-buffer-name-style 'post-forward-angle-brackets)

;; ---------------------------------------------------------------- ;;
;; Toggle reverse video
;;
;; From http://lists.gnu.org/archive/html/help-gnu-emacs/2011-03/msg00818.html
;;

(GNUEmacs
 (defun toggle-rev-video()
   "Toggle reverse video"
   (interactive)
   (x-handle-reverse-video (selected-frame) '((reverse . t))))
 (global-set-key "\C-cv" 'toggle-rev-video))

;;; ---------------------------------------------------------------- ;;
;
;(defun toggle-trunc-lines ()
;  "toggles truncate-lines variable between nil and non-nil for this buffer"
;  (interactive)
;  (if truncate-lines
;    (setq truncate-lines nil)
;    (setq truncate-lines 1)))
;
;;; ---------------------------------------------------------------- ;;
;; I don't think I need these
;
;(setq search-highlight t)              ;; highlight search strings
;;(Windows (require 'cygwin32-mount))   ;; read cygwin mount points
;(GNUEmacs (transient-mark-mode 1))      ;; highlight region when mark is active
;(setq next-line-add-newlines nil)      ;; no newlines at end of buffer
;(setq scroll-step 3)                   ;; set scrolling
;(setq make-backup-files nil)           ;; no *~ files
;(setq angry-mob-with-torches-and-pitchforks t)
;(GNUEmacs (menu-bar-mode -1))          ;; turn off menu bar
;(resize-minibuffer-mode 1)             ;; automatically resize minibuffer
;(hscroll-global-mode)                  ;; horizontal scroll
;(set-input-mode nil nil t)             ;; use accents
;(setq default-major-mode 'text-mode)   ;; text mode as default
;(setq find-file-existing-other-name t) ;; handle symbolic links
;(setq-default mode-line-mule-info "-")
;(setq display-time-mail-file t)        ;; don't check for new mail
;
;; ---------------------------------------------------------------- ;;
;; Cscope
;;
;(require 'xcscope)
;(add-hook 'java-mode-hook (function cscope:hook))
;(cscope-set-initial-directory "/u/yuanc/usr/tags")
;
;;
;; Cscope Keybindings (from man xcscope):
;;
;; All keybindings use the "C-c s" prefix, but are usable only while
;; editing a source file, or in the cscope results buffer:
;;
;; C-c s s Find symbol.
;; C-c s d Find global definition.
;; C-c s g Find global definition (alternate binding).
;; C-c s G Find global definition without prompting.
;; C-c s c Find functions calling a function.
;; C-c s C Find called functions (list functions called from a function).
;; C-c s t Find text string.
;; C-c s e Find egrep pattern.
;; C-c s f Find a file.
;; C-c s i Find files #including a file.
;;
;; These pertain to navigation through the search results:
;;
;; C-c s b Display *cscope* buffer.
;; C-c s B Auto display *cscope* buffer toggle.
;; C-c s n Next symbol.
;; C-c s N Next file.
;; C-c s p Previous symbol.
;; C-c s P Previous file.
;; C-c s u Pop mark.
;;
;; These pertain to setting and unsetting the variable,
;; 'cscope-initial-directory', (location searched for the cscope
;; database directory):
;;
;; C-c s a Set initial directory.
;; C-c s A Unset initial directory.
;;
;; These pertain to cscope database maintenance:
;;
;; C-c s L Create list of files to index.
;; C-c s I Create list and index.
;; C-c s E Edit list of files to index.
;; C-c s W Locate this buffer's cscope directory  ( "W" --> "where" ).
;; C-c s S Locate this buffer's cscope directory. (alternate binding: "S" --> "show" ).
;; C-c s T Locate this buffer's cscope directory. (alternate binding: "T" --> "tell" ).
;; C-c s D Dired this buffer's directory.
;;
;; ---------------------------------------------------------------- ;;
;; Change default colors
;;

;; (defun fontify ()
;;   "Turn on font lock (M-x list-faces-display) and customize colors."
;;   (interactive)
;;   (require 'font-lock)       ; for xemacs
;;   (if (functionp 'global-font-lock-mode) (global-font-lock-mode t))
;;   ;(setq font-lock-support-mode 'lazy-lock-mode)
;;   (setq lazy-lock-minimum-size 10000)
;;   (setq lazy-lock-defer-on-scrolling 'eventually)
;;   (setq lazy-lock-stealth-time 5)
;;   (setq lazy-lock-defer-contextually t)
;;   (setq font-lock-maximum-decoration t)
;;   (set-face-foreground 'bold "blue")
;;   (set-face-foreground 'italic "purple")
;;   (set-face-foreground 'bold-italic "red2")
;;   (set-face-foreground 'underline "Magenta")
;;   (if (x-display-color-p)
;;       (set-face-underline-p 'underline nil))
;;   (if (< (string-to-number emacs-version) 20)
;;       (setq font-lock-face-attributes
;;          '((font-lock-comment-face "forest green")
;;            (font-lock-function-name-face "red")
;;            (font-lock-keyword-face "blue")
;;            (font-lock-reference-face "cadetblue")
;;            (font-lock-string-face "brown")
;;            (font-lock-type-face "purple")
;;            (font-lock-variable-name-face "orangered")))
;;     (if (facep 'font-lock-builtin-face)
;;      (set-face-foreground 'font-lock-builtin-face "Orchid"))
;;     (set-face-foreground 'font-lock-comment-face "forest green")
;;     (if (facep 'font-lock-reference-face)
;;      (set-face-foreground 'font-lock-reference-face "cadetblue"))
;;     (if (not (facep 'font-lock-constant-face))
;;      (copy-face 'font-lock-reference-face 'font-lock-constant-face))
;;     (set-face-foreground 'font-lock-constant-face "cadetblue")
;;     (set-face-foreground 'font-lock-function-name-face "red")
;;     (set-face-foreground 'font-lock-keyword-face "blue")
;;     (set-face-foreground 'font-lock-string-face "brown")
;;     (set-face-foreground 'font-lock-type-face "purple")
;;     (set-face-foreground 'font-lock-variable-name-face "orangered")
;;     (if (facep 'font-lock-warning-face)
;;      (set-face-foreground 'font-lock-warning-face "red"))
;;     (GNUEmacs (set-face-foreground 'modeline "white")
;;            (set-face-background 'modeline "steel blue"))
;;     (XEmacs (set-face-foreground 'modeline "red")
;;          (set-face-background 'modeline "Gray95"))
;;     (XEmacs (set-face-background 'default "gray85"))
;;     ; change font-lock-keywords
;;     (GNUEmacs
;;      (font-lock-add-keywords 'tcl-mode
;;       '(("\\<\\(set\\|unset\\|incr\\|expr\\|array\\|split\\|string\\|regexp\\|array\\|lindex\\|list\\|lappend\\)\\>"
;;       0 font-lock-type-face)
;;      ("\\<\\(catch\\)\\>" 0 font-lock-keyword-face)
;;      ("${?\\(\\sw+\\)" 1 font-lock-variable-name-face) ; variables
;;      ("$\\(\\sw+\\)(\\(\\sw+\\))" 2 font-lock-variable-name-face) ; array variables
;;      ("\\<[0-9]+\\>" 0 'font-lock-constant-face)
;;      ("\\<0x[0-9]+\\>" 0 'font-lock-constant-face)
;;      ; itcl stuff
;;      ("\\<private\\>" 0 font-lock-type-face)
;;      ("\\<\\(namespace\\)\\>[        ]*\\(\\sw+\\)?"
;;       (1 font-lock-type-face)
;;       (2 font-lock-function-name-face nil t))
;;      ("\\<\\(body\\|class\\|configbody\\|variable\\)\\>[     ]*\\(\\sw+\\)?"
;;       (1 font-lock-keyword-face)
;;       (2 font-lock-function-name-face nil t))
;;      ("#auto" 0 'font-lock-type-face t)
;;      ))
;;     (font-lock-add-keywords 'perl-mode
;;       '(("^\\(=\\sw+\\)\\s-\\(.+\\)\n\\(^\n\\|^[^=].*\n\\)*"
;;       (0 font-lock-comment-face prepend)
;;       (1 font-lock-builtin-face prepend)
;;       (2 font-lock-type-face prepend))
;;      ("^=cut$" 0 font-lock-builtin-face)))
;;     (font-lock-add-keywords 'comint-mode
;;       '(("^\\[[0-9]+\\][^#$%>\n]*[$>] *" 0 font-lock-keyword-face))))))

;; (if window-system
;;     (fontify))

;; ---------------------------------------------------------------- ;;
