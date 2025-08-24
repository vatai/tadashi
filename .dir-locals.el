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
                           (let ((python-path-env (getenv "PYTHONPATH")))
                             (setq-local process-environment
                                         (cons
                                          (concat "PYTHONPATH="
                                                  (projectile-project-root)
                                                  (if python-path-env
                                                      (concat ":" python-path-debenv)
                                                    ""))
                                          process-environment))))))))
