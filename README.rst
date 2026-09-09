n8n plugin for `Tutor <https://docs.tutor.edly.io>`__
#####################################################

n8n plugin for Tutor

This plugin adds a self-hosted `n8n <https://n8n.io>`__ instance to your
Tutor-based Open edX platform (following the official
`n8n-docker-caddy <https://github.com/n8n-io/n8n-docker-caddy>`__ deployment
model, adapted to Tutor's own Caddy reverse proxy), and installs
`openedx-events-2-n8n <https://github.com/Abstract-Tech/openedx-events-2-n8n>`__
in the LMS/CMS image so that registration, enrollment, and grade-change
Open edX Events are forwarded to n8n webhooks.

Installation
************

.. code-block:: bash
    pip install tutor-contrib-n8n
    # or, to install the latest development version:
    pip install git+https://github.com/Abstract-Tech/tutor-contrib-n8n

Usage
*****

.. code-block:: bash

    tutor plugins enable n8n
    tutor config save
    tutor local launch

n8n will be reachable at ``https://n8n.<LMS_HOST>`` (or ``http://`` when
``ENABLE_HTTPS`` is disabled), and the ``openedx-events-2-n8n`` package will
be installed in the ``openedx`` image automatically. The same manifests are
provided for ``tutor k8s launch`` (a ``Deployment``, ``Service`` and
``PersistentVolumeClaim`` are created for n8n, and routed through the same
Caddy reverse proxy), **but this Kubernetes configuration is untested** — it
has not been deployed or verified on a real cluster. Treat it as a starting
point, not a validated deployment path.

Once n8n is running, create your webhook workflows and configure their URLs
either via the Django admin
(``/admin/openedx_events_2_n8n/webhookconfig/``) or via the settings below.

Configuration
*************

All settings are prefixed with ``N8N_`` and can be set with
``tutor config save --set N8N_SETTING=value``.

n8n service
===========

======================================= ========================================================= ==============================================
Setting                                 Default                                                   Description
======================================= ========================================================= ==============================================
``N8N_DOCKER_IMAGE``                    ``docker.n8n.io/n8nio/n8n:latest``                       Docker image used for the n8n container.
``N8N_HOST``                            ``n8n.{{ LMS_HOST }}``                                   Domain name at which n8n is exposed.
``N8N_PORT``                            ``5678``                                                 Port n8n listens on inside its container.
``N8N_GENERIC_TIMEZONE``                ``UTC``                                                  Timezone used by n8n for scheduling.
``N8N_ENCRYPTION_KEY``                  randomly generated                                       Key n8n uses to encrypt stored credentials.
``N8N_K8S_STORAGE``                     ``1Gi``                                                  Size of the n8n ``PersistentVolumeClaim`` (k8s only).
======================================= ========================================================= ==============================================

n8n data (workflows, credentials) is persisted in the ``n8n`` bind-mounted
data volume (``tutor local``) or ``PersistentVolumeClaim`` (``tutor k8s``),
alongside Tutor's other services.

openedx-events-2-n8n
=====================

============================================= ========= ===========================================================
Setting                                       Default   Description
============================================= ========= ===========================================================
``N8N_OPENEDX_EVENTS_ENABLED``                ``True``  Install ``openedx-events-2-n8n`` in the openedx image and
                                                         write the ``N8N_*_WEBHOOK`` values below into the LMS/CMS
                                                         Django settings. The package also ships a
                                                         ``WebhookConfig`` model, configurable from the Django
                                                         admin, as an alternative to these settings-based URLs.
``N8N_OPENEDX_EVENTS_VERSION``                ``0.5.0`` Version of ``openedx-events-2-n8n`` (PyPI) to install.
``N8N_REGISTRATION_WEBHOOK``                  ``""``    n8n webhook URL for ``STUDENT_REGISTRATION_COMPLETED``.
``N8N_ENROLLMENT_WEBHOOK``                    ``""``    n8n webhook URL for ``COURSE_ENROLLMENT_CREATED``.
``N8N_PERSISTENT_GRADE_COURSE_WEBHOOK``       ``""``    n8n webhook URL for ``PERSISTENT_GRADE_SUMMARY_CHANGED``.
============================================= ========= ===========================================================

These webhook URLs are only a fallback: a ``WebhookConfig`` entry created in
the Django admin for a given event takes priority when present.

Set ``N8N_OPENEDX_EVENTS_ENABLED=false`` to run the n8n service without
installing the Open edX events integration.

Development
***********

.. code-block:: bash

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    make test

License
*******

This software is licensed under the terms of the AGPLv3.
