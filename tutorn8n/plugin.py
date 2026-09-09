import os
from glob import glob

import importlib_resources
from tutor import hooks

from .__about__ import __version__

########################################
# CONFIGURATION
########################################

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        ("N8N_VERSION", __version__),
        # n8n service
        # Pinned, not "latest" - "latest" drifts: two installs on different days get
        # different n8n versions, so bugs/behavior become irreproducible across users.
        # To verify what "latest" currently points to before bumping this pin:
        #   curl -s https://api.github.com/repos/n8n-io/n8n/releases/latest | jq -r .tag_name
        #   curl -s https://hub.docker.com/v2/namespaces/n8nio/repositories/n8n/tags/latest | jq -r '.images[].digest'
        #   curl -s https://hub.docker.com/v2/namespaces/n8nio/repositories/n8n/tags/<VERSION> | jq -r '.images[].digest'
        #   # digests must match; that <VERSION> is what "latest" currently resolves to
        ("N8N_DOCKER_IMAGE", "docker.n8n.io/n8nio/n8n:2.38.5"),
        ("N8N_HOST", "n8n.{{ LMS_HOST }}"),
        ("N8N_PORT", 5678),
        ("N8N_GENERIC_TIMEZONE", "UTC"),
        ("N8N_K8S_STORAGE", "1Gi"),
        # Cookies only sent over HTTPS; local/prod sit behind Caddy with TLS.
        # dev mode overrides this to false since it runs without TLS.
        ("N8N_SECURE_COOKIE", True),
        # Disable telemetry phoning home to n8n.io by default.
        ("N8N_DIAGNOSTICS_ENABLED", False),
        # openedx-events-2-n8n: forwards Open edX events to n8n webhooks
        ("N8N_OPENEDX_EVENTS_ENABLED", True),
        ("N8N_OPENEDX_EVENTS_VERSION", "0.5.0"),
        ("N8N_REGISTRATION_WEBHOOK", ""),
        ("N8N_ENROLLMENT_WEBHOOK", ""),
        ("N8N_PERSISTENT_GRADE_COURSE_WEBHOOK", ""),
        # Owner account, created automatically by the init task.
        ("N8N_ADMIN_EMAIL", "admin@example.com"),
        ("N8N_ADMIN_FIRST_NAME", "Admin"),
        ("N8N_ADMIN_LAST_NAME", "User"),
    ]
)

hooks.Filters.CONFIG_UNIQUE.add_items(
    [
        # Encrypts credentials n8n stores at rest; must stay stable across restarts.
        ("N8N_ENCRYPTION_KEY", "{{ 24|random_string }}"),
        # Signs session JWTs; if unset n8n regenerates it on every restart,
        # invalidating all logged-in sessions.
        ("N8N_USER_MANAGEMENT_JWT_SECRET", "{{ 24|random_string }}"),
        ("N8N_ADMIN_PASSWORD", "{{ 16|random_string }}A1!"),
    ]
)

hooks.Filters.CONFIG_OVERRIDES.add_items(
    [
        # Danger zone!
        # Add values to override settings from Tutor core or other plugins here.
        # Each override is a pair: (setting_name, new_value). For example:
        ### ("PLATFORM_NAME", "My platform"),
    ]
)


########################################
# INITIALIZATION TASKS
########################################

# To add a custom initialization task, create a bash script template under:
# tutorn8n/templates/n8n/tasks/
# and then add it to the MY_INIT_TASKS list. Each task is in the format:
# ("<service>", ("<path>", "<to>", "<script>", "<template>"))
MY_INIT_TASKS: list[tuple[str, tuple[str, ...]]] = [
    # Creates the n8n owner account via the REST API, so it doesn't have
    # to be done manually through the setup wizard on first load.
    ("n8n", ("n8n", "tasks", "n8n", "init.sh")),
]


# For each task added to MY_INIT_TASKS, we load the task template
# and add it to the CLI_DO_INIT_TASKS filter, which tells Tutor to
# run it as part of the `init` job.
for service, template_path in MY_INIT_TASKS:
    full_path: str = str(
        importlib_resources.files("tutorn8n")
        / os.path.join("templates", *template_path)
    )
    with open(full_path, encoding="utf-8") as init_task_file:
        init_task: str = init_task_file.read()
    hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, init_task))


########################################
# DOCKER IMAGE MANAGEMENT
########################################


# Images to be built by `tutor images build`.
# Each item is a quadruple in the form:
#     ("<tutor_image_name>", ("path", "to", "build", "dir"), "<docker_image_tag>", "<build_args>")
hooks.Filters.IMAGES_BUILD.add_items(
    [
        # To build `myimage` with `tutor images build myimage`,
        # you would add a Dockerfile to templates/n8n/build/myimage,
        # and then write:
        ### (
        ###     "myimage",
        ###     ("plugins", "n8n", "build", "myimage"),
        ###     "docker.io/myimage:{{ N8N_VERSION }}",
        ###     (),
        ### ),
    ]
)


# Images to be pulled as part of `tutor images pull`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PULL.add_items(
    [
        (
            "n8n",
            "{{ N8N_DOCKER_IMAGE }}",
        ),
    ]
)


# Images to be pushed as part of `tutor images push`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PUSH.add_items(
    [
        # To push `myimage` with `tutor images push myimage`, you would write:
        ### (
        ###     "myimage",
        ###     "docker.io/myimage:{{ N8N_VERSION }}",
        ### ),
    ]
)


########################################
# TEMPLATE RENDERING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

hooks.Filters.ENV_TEMPLATE_ROOTS.add_items(
    # Root paths for template files, relative to the project root.
    [
        str(importlib_resources.files("tutorn8n") / "templates"),
    ]
)

hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    # For each pair (source_path, destination_path):
    # templates at ``source_path`` (relative to your ENV_TEMPLATE_ROOTS) will be
    # rendered to ``source_path/destination_path`` (relative to your Tutor environment).
    # For example, ``tutorn8n/templates/n8n/build``
    # will be rendered to ``$(tutor config printroot)/env/plugins/n8n/build``.
    [
        ("n8n/build", "plugins"),
        ("n8n/apps", "plugins"),
    ],
)


########################################
# PATCH LOADING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

# For each file in tutorn8n/patches,
# apply a patch based on the file's name and contents.
for path in glob(str(importlib_resources.files("tutorn8n") / "patches" / "*")):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))


########################################
# CUSTOM JOBS (a.k.a. "do-commands")
########################################

# A job is a set of tasks, each of which run inside a certain container.
# Jobs are invoked using the `do` command, for example: `tutor local do importdemocourse`.
# A few jobs are built in to Tutor, such as `init` and `createuser`.
# You can also add your own custom jobs:


# To add a custom job, define a Click command that returns a list of tasks,
# where each task is a pair in the form ("<service>", "<shell_command>").
# For example:
### @click.command()
### @click.option("-n", "--name", default="plugin developer")
### def say_hi(name: str) -> list[tuple[str, str]]:
###     """
###     An example job that just prints 'hello' from within both LMS and CMS.
###     """
###     return [
###         ("lms", f"echo 'Hello from LMS, {name}!'"),
###         ("cms", f"echo 'Hello from CMS, {name}!'"),
###     ]


# Then, add the command function to CLI_DO_COMMANDS:
## hooks.Filters.CLI_DO_COMMANDS.add_item(say_hi)

# Now, you can run your job like this:
#   $ tutor local do say-hi --name="Abstract Technology GmbH"


#######################################
# CUSTOM CLI COMMANDS
#######################################

# Your plugin can also add custom commands directly to the Tutor CLI.
# These commands are run directly on the user's host computer
# (unlike jobs, which are run in containers).

# To define a command group for your plugin, you would define a Click
# group and then add it to CLI_COMMANDS:


### @click.group()
### def n8n() -> None:
###     pass


### hooks.Filters.CLI_COMMANDS.add_item(n8n)


# Then, you would add subcommands directly to the Click group, for example:


### @n8n.command()
### def example_command() -> None:
###     """
###     This is helptext for an example command.
###     """
###     print("You've run an example command.")


# This would allow you to run:
#   $ tutor n8n example-command
