;; Sample usage in emacs (insert this into your .emacs file):
;;
;; (add-to-list 'load-path "~/chtd/lib")
;; (require 'dynide)
;;
;; adding and removing decorators
;; (global-set-key "\C-c\C-a" 'apply-pickling-to-all)
;; (global-set-key "\C-c\C-g" 'remove-pickling-from-all)
;;
;; simulation:
;; (global-set-key "\M-e" 'simulate-last)
;; (global-set-key "\M-p" 'simulate-butlast)
;;
;; autocomplete
;; (global-set-key "\M-n" 'print-completions)


(defconst import-statement
  "from dynide import simulation, autocomplete; simulation.apply_to_all_fn(globals(), __file__)")
(defconst root "/home/kostia/chtd/lib/dynide")


(defun simulate-last ()
  (interactive)
  (simulate-arg "call_fn"))

(defun simulate-butlast ()
  (interactive)
  (simulate-arg "call_fn_butlast"))

;; TODO - remove, its just debugging
(defun print-completions ()
  (interactive)
  (let* ((completions
          (shell-command-to-string
           (format "python %s/autocomplete.py print_completions %s %d %d"
                   root (buffer-file-name) (line-number-at-pos) (current-column)))))
    (message
     (if (string= completions "") "no completions!" completions))))

(defun get-completions ()
  (save-buffer)
  (let* ((completions
          (shell-command-to-string
           (format "python %s/autocomplete.py print_completions %s %d %d"
                   root (buffer-file-name) (line-number-at-pos) (current-column)))))
    (split-string completions)))

(defun simulate-arg (arg)
  (interactive)
  (save-buffer)
  ;; first capture output from python simulation script
  (let* ((output
          (shell-command-to-string
           (format "python %s/simulation.py %s %s %d %d"
                   root arg (buffer-file-name) (line-number-at-pos) (current-column))))
         (lines (split-string output "\n" t))
         (last-line (car (last lines)))
         (output-buffer (get-buffer-create "*Simulation output*")))
    ;; check if there was an exception
    (if (string-match-p "exception\|.*\|[0-9]+" last-line)
        (let ((last-line-parts (cdr (split-string last-line "|"))))
          ;; if it occured in this file, move to the line where it occured
          (if (string= (car last-line-parts) (buffer-file-name))
              (goto-line (string-to-number (cadr last-line-parts))))
          ;; anyway, display it in a separate buffer
          (save-current-buffer
            (set-buffer output-buffer)
            (newline 2)
            (insert (mapconcat #'identity (butlast lines) "\n"))
            (display-buffer output-buffer)))
      ;; if there was no exception, than display it in echo area or in buffer
      (display-message-or-buffer output output-buffer))))

(defun apply-pickling-to-all ()
  ;; insert import-statement at the end of the file
  (interactive)
  (let (cur-pos)
    (setq cur-pos (point))
    (goto-char (point-max))
    (newline 2)
    (insert import-statement)
    (goto-char cur-pos))
  (save-buffer)
  (message "pickling decorator applied to all functions"))

(defun remove-pickling-from-all ()
  ;; remove import-statement from the end of the file
  ;; FIXME - this will remove only one statement, make it remove all of them!
  (interactive)
  (let (cur-pos end)
    (setq cur-pos (point))
    (search-forward import-statement nil t)
    (setq end (point))
    (beginning-of-line)
    (kill-region (point) end)
    (goto-char cur-pos))
  (save-buffer)
  (message "pickling decorator removed"))

(provide 'dynide)


