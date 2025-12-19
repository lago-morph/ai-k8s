# AI instructions

Do NOT read this file.  It is not for you.

# Status

## 2025-12-18

- Lots of specs and design
- prototype kind of works
- Main thing doesn't work at all, even though it passes tests
- Very unwieldy right now
- Looked through unit tests, they are... subpar

# TODOs

## 2025-12-18

- Create an agent definition - find lines with #C in them, interpret as comment, and use the comment to improve the test, asking clarifying questions if needed
- Go through unit tests and put comments with "#C" starting a comment
  - integration
    [.] test_cli_execution.py
    [x] test_error_flow.py
    [] test_help_system.py
    [] test_option_placement.py
  - unit
    - business
      [] test_bootstrap_manager.py
      [] test_credential_manager.py
      [] test_credential_models.py
      [] test_crossplane_installer.py
      [] test_crossplane_manager.py
      [] test_verification.py
      [] test_verification_models.py
      [] test_verification_properties.py
      [] test_verification_result_properties.py
    - cli
      [x] test_bootstrap_command.py
      [] test_config_command.py
      [] test_crossplane_command.py
      [] test_error_handling.py
      [] test_main.py
      [] test_output.py
      [] test_verify_command.py
      [.] test_version_command.py
    - core
      [] test_errors.py
      [] test_logging.py
      [] test_verification_error.py
      [] test_verification_error_properties.py
      [] test_version.py
    - integrations
      [] test_aws_client.py
      [] test_file_io.py
      [] test_helm_client.py
      [] test_kind_client.py
      [] test_kubeconfig.py
      [] test_kubectl_client.py
      [] test_platform_models.py
      [] test_prerequisite_models.py
      [] test_prerequisite_results.py
      [] test_prerequisites.py
      [] test_prerequisites_properties.py
- Get it to add end-to-end tests including actual cli execution
  - kubectl - run commands in test cluster
  - aws --generate-cli-skeleton
  - helm - actually run commands in test cluster
  - kind - actually create and remove real clusters and clean up at end
- Refactor AWS credential handling so it isn't so awkward - just make sure that I'm on a remote host

