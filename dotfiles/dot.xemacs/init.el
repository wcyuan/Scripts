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
;; M-g       -- goto line number
;; M-<       -- goto beginning of file
;; M->       -- goto end of file
;;
;; C-s       -- search
;; C-r       -- backwards search
;;
;; M-<del>   -- kill (cut) previous word
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
;; M-space   -- begin marking a region.  Also just shift-<arrow>
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
;; C-u <n>   -- repeat a command <n> times.  <n> defaults to 4
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
(setq enable-local-variables t)		;; Let files specify major-mode
(setq-default indent-tabs-mode nil)     ;; Indent with spaces, not tabs
(setq inhibit-startup-message t)	;; No emacs start-up message
(setq dired-listing-switches (concat dired-listing-switches "F"))
(put 'narrow-to-region 'disabled nil)	;; Enable C-x-n-n
(setq diff-switches "-wu")              ;; Switches to pass to diff
(setq require-final-newline t)          ;; Always make sure files end
                                        ;; with newlines

;; customize mode line
(setq display-time-string-forms '((format "%s:%s%s" 12-hours minutes am-pm)))
(display-time)				;; Show current time

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

;; use bash-mode for .bashrc
(setq auto-mode-alist (append '(("\\.bashrc\\'" . bash-mode)
                                )
                              auto-mode-alist))

;; ---------------------------------------------------------------- ;;
;; Perl
;;
; http://www.emacswiki.org/emacs/CPerlMode
;; cperl-mode is preferred to perl-mode
;; "Brevity is the soul of wit" <foo at acm.org>
(defalias 'perl-mode 'cperl-mode)

; http://www.emacswiki.org/emacs/IndentingPerl
(setq cperl-indent-level 4
      cperl-continued-statement-offset 4
      ;cperl-close-paren-offset -4
      ;cperl-indent-parens-as-block t
      ;cperl-tab-always-indent t
      )

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

;;; Put backups in another directory.  With the directory-info
;;; variable, you can control which files get backed up where.
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
(setq-default delete-old-versions t)

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
        (setq show-trailing-whitespace t))))
(global-set-key "\C-cw" 'toggle-trailing-whitespace)

;; ---------------------------------------------------------------- ;;
;; Matlab mode
;;
(add-to-list 'load-path "~/.xemacs/matlab-emacs/matlab-emacs/")
(require 'matlab-load)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; ---------------------------------------------------------------- ;;
;;;
;;; Tags
;;;
;
; ;; M-.     -- search for a tag
; ;; M-,     -- go to next result in the tag search
;
;(setq tags-file-name '"/u/yuanc/usr/tags/TAGS")
;(setq tags-build-completion-table t)
;(setq tags-auto-read-changed-tag-files t)
;(setq tags-always-exact t)		;; make tags work "correctly"
;(Unix (setq tags-table-list '("/u/yuanc/usr/tags/TAGS")))
;(if (>= (emacs-number) 20.3)
;    (setq tags-revert-without-query t)	;; always revert tags tables w/o query
;  (setq revert-without-query '(".*")))	;; always revert tags tables w/o query
;
;
;;; ---------------------------------------------------------------- ;;
;;;
;;; Column Marker
;;;
;;; http://www.emacswiki.org/emacs/ColumnMarker
;;;
;(require 'column-marker)
;
;(defun set-eighty-column ()
;  "Highlight the 80th column"
;  (interactive)
;  (if column-marker-1
;      (column-marker-internal 'column-marker-1 nil)
;      (column-marker-1 80)))
;
;; \C-c\C-e seems to be a neat double paren feature, at least in
;; cperl, so don't override it.
;;(global-set-key "\C-c\C-e" 'set-eighty-column)
;;(global-set-key "\M-n" 'just-one-space)
;;(global-set-key "\M-p" 'fill-paragraph)
;
;(global-set-key "\C-c8" 'set-eighty-column)
;
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
;(setq search-highlight t)		;; highlight search strings
;;(Windows (require 'cygwin32-mount))	;; read cygwin mount points
;(GNUEmacs (transient-mark-mode 1))      ;; highlight region when mark is active
;(setq next-line-add-newlines nil)	;; no newlines at end of buffer
;(setq scroll-step 3)			;; set scrolling
;(setq make-backup-files nil)		;; no *~ files
;(setq angry-mob-with-torches-and-pitchforks t)
;(GNUEmacs (menu-bar-mode -1))		;; turn off menu bar
;(resize-minibuffer-mode 1)		;; automatically resize minibuffer
;(hscroll-global-mode)			;; horizontal scroll
;(set-input-mode nil nil t)		;; use accents
;(setq default-major-mode 'text-mode)	;; text mode as default
;(setq find-file-existing-other-name t)	;; handle symbolic links
;(setq-default mode-line-mule-info "-")
;(setq display-time-mail-file t)	;; don't check for new mail
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
;;   (require 'font-lock)	; for xemacs
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
;; 	    '((font-lock-comment-face "forest green")
;; 	      (font-lock-function-name-face "red")
;; 	      (font-lock-keyword-face "blue")
;; 	      (font-lock-reference-face "cadetblue")
;; 	      (font-lock-string-face "brown")
;; 	      (font-lock-type-face "purple")
;; 	      (font-lock-variable-name-face "orangered")))
;;     (if (facep 'font-lock-builtin-face)
;; 	(set-face-foreground 'font-lock-builtin-face "Orchid"))
;;     (set-face-foreground 'font-lock-comment-face "forest green")
;;     (if (facep 'font-lock-reference-face)
;; 	(set-face-foreground 'font-lock-reference-face "cadetblue"))
;;     (if (not (facep 'font-lock-constant-face))
;; 	(copy-face 'font-lock-reference-face 'font-lock-constant-face))
;;     (set-face-foreground 'font-lock-constant-face "cadetblue")
;;     (set-face-foreground 'font-lock-function-name-face "red")
;;     (set-face-foreground 'font-lock-keyword-face "blue")
;;     (set-face-foreground 'font-lock-string-face "brown")
;;     (set-face-foreground 'font-lock-type-face "purple")
;;     (set-face-foreground 'font-lock-variable-name-face "orangered")
;;     (if (facep 'font-lock-warning-face)
;; 	(set-face-foreground 'font-lock-warning-face "red"))
;;     (GNUEmacs (set-face-foreground 'modeline "white")
;; 	      (set-face-background 'modeline "steel blue"))
;;     (XEmacs (set-face-foreground 'modeline "red")
;; 	    (set-face-background 'modeline "Gray95"))
;;     (XEmacs (set-face-background 'default "gray85"))
;;     ; change font-lock-keywords
;;     (GNUEmacs
;;      (font-lock-add-keywords 'tcl-mode
;;       '(("\\<\\(set\\|unset\\|incr\\|expr\\|array\\|split\\|string\\|regexp\\|array\\|lindex\\|list\\|lappend\\)\\>"
;; 	 0 font-lock-type-face)
;; 	("\\<\\(catch\\)\\>" 0 font-lock-keyword-face)
;; 	("${?\\(\\sw+\\)" 1 font-lock-variable-name-face) ; variables
;; 	("$\\(\\sw+\\)(\\(\\sw+\\))" 2 font-lock-variable-name-face) ; array variables
;; 	("\\<[0-9]+\\>" 0 'font-lock-constant-face)
;; 	("\\<0x[0-9]+\\>" 0 'font-lock-constant-face)
;; 	; itcl stuff
;; 	("\\<private\\>" 0 font-lock-type-face)
;; 	("\\<\\(namespace\\)\\>[ 	]*\\(\\sw+\\)?"
;; 	 (1 font-lock-type-face)
;; 	 (2 font-lock-function-name-face nil t))
;; 	("\\<\\(body\\|class\\|configbody\\|variable\\)\\>[ 	]*\\(\\sw+\\)?"
;; 	 (1 font-lock-keyword-face)
;; 	 (2 font-lock-function-name-face nil t))
;; 	("#auto" 0 'font-lock-type-face t)
;; 	))
;;     (font-lock-add-keywords 'perl-mode
;;       '(("^\\(=\\sw+\\)\\s-\\(.+\\)\n\\(^\n\\|^[^=].*\n\\)*"
;; 	 (0 font-lock-comment-face prepend)
;; 	 (1 font-lock-builtin-face prepend)
;; 	 (2 font-lock-type-face prepend))
;; 	("^=cut$" 0 font-lock-builtin-face)))
;;     (font-lock-add-keywords 'comint-mode
;;       '(("^\\[[0-9]+\\][^#$%>\n]*[$>] *" 0 font-lock-keyword-face))))))

;; (if window-system
;;     (fontify))

;; ---------------------------------------------------------------- ;;
;; Flymake
;;
;; http://www.gnu.org/software/emacs/manual/html_mono/flymake.html
;; http://www.emacswiki.org/emacs/PythonMode#toc8
;;

;; (when (load "flymake" t)
;;   (defun flymake-pylint-init ()
;;     (let* ((temp-file (flymake-init-create-temp-buffer-copy
;;                        'flymake-create-temp-inplace))
;;        (local-file (file-relative-name
;;                     temp-file
;;                     (file-name-directory buffer-file-name))))
;;       (list "epylint" (list local-file))))

;;   (add-to-list 'flymake-allowed-file-name-masks
;;            '("\\.py\\'" flymake-pylint-init)))

;; (setq flymake-allowed-file-name-masks
;;       '(("\\.py\\'" flymake-pylint-init)
;;         ("\\.html?\\'" flymake-xml-init)
;;         ("\\.cs\\'" flymake-simple-make-init)
;;         ("\\.pl\\'" flymake-perl-init)
;;         ("[0-9]+\\.tex\\'" flymake-master-tex-init flymake-master-cleanup)
;;         ("\\.tex\\'" flymake-simple-tex-init)
;;         ("\\.idl\\'" flymake-simple-make-init)))
;; ; remove the c, java, and xml flymake hooks since those don't seem to work.
;;   ;("\\.c\\'" flymake-simple-make-init)
;;   ;("\\.cpp\\'" flymake-simple-make-init)
;;   ;("\\.xml\\'" flymake-xml-init)
;;   ;("\\.h\\'" flymake-master-make-header-init flymake-master-cleanup)
;;   ;("\\.java\\'" flymake-simple-make-java-init flymake-simple-java-cleanup)

;; (add-hook 'find-file-hook 'flymake-find-file-hook)

;; ---------------------------------------------------------------- ;;
