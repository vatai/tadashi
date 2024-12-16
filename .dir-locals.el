((nil
  . ((eglot-workspace-configuration
      . (:pylsp
         (:plugins
          (:jedi_completion
           (:include_params t :fuzzy t)
           :pylint
           (:enabled :json-false)))
                ;; :gopls (:usePlaceholders t)
                ))))
 ;; (python-base-mode . ((indent-tabs-mode . nil)))
 ;; (go-mode          . ((indent-tabs-mode . t)))
 (python-mode . ((eval . (progn
                           (let ((project_path
                                  (car (dir-locals-find-file
                                        (buffer-file-name))))
                                 (python_path_env (getenv "PYTHONPATH")))
                             (setq-local process-environment
                                         (cons
                                          (concat "PYTHONPATH="
                                                  project_path
                                                  (if python_path_env
                                                      (concat ":" python_path_env)
                                                    ""))
                                          process-environment))))))))
