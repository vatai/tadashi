((nil
  . ((eglot-workspace-configuration
      . (:pylsp
         (:plugins
          (:jedi_completion
           (:include_params t :fuzzy t)
           :pylint
           (:enabled :json-false)))
                ;; :gopls (:usePlaceholders t)
         ))
     (projectile-project-compilation-cmd
      . "./setup.py build_ext -i")
     (projectile-project-test-cmd
      ;; . "python -m unittest tests.test_translators.TestPolly.test_wip")
      . "python -m unittest tests.test_apps.TestPolybench.test_end2end_polly")
     (corfu-auto
      . t))
  )
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
