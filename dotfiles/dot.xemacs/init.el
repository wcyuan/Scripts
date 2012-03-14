;; -------------------------------------------------
;; Bash mode

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

;; -------------------------------------------------
;; VC

(require 'vc)

;; -------------------------------------------------
;; Backups and auto-saves
;;
;; from http://snarfed.org/gnu_emacs_backup_files
;;

;;; Auto-save
;;; Load the auto-save.el package, which lets you put all of your autosave
;;; files in one place, instead of scattering them around the file system.
;;; M-x recover-all-files or M-x recover-file to get them back
(defvar temp-directory "~/.xemacs/tmp")
(make-directory temp-directory t)

; One of the main issues for me is that my home directory is
; NFS mounted.  By setting all the autosave directories in /tmp,
; things run much quicker
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

