# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2012 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import webob.exc

from nova.api.openstack import extensions
from nova.api.openstack import wsgi
import nova.cert.rpcapi
from nova import exception
from nova import network
from nova.openstack.common.gettextutils import _

ALIAS = "os-certificates"
authorize = extensions.extension_authorizer('compute', 'v3:' + ALIAS)


def _translate_certificate_view(certificate, private_key=None):
    return {
        'data': certificate,
        'private_key': private_key,
    }


class CertificatesController(object):
    """The x509 Certificates API controller for the OpenStack API."""

    def __init__(self):
        self.network_api = network.API()
        self.cert_rpcapi = nova.cert.rpcapi.CertAPI()
        super(CertificatesController, self).__init__()

    @extensions.expected_errors((404, 501))
    def show(self, req, id):
        """Return certificate information."""
        context = req.environ['nova.context']
        authorize(context)
        if id != 'root':
            msg = _("Only root certificate can be retrieved.")
            raise webob.exc.HTTPNotImplemented(explanation=msg)
        try:
            cert = self.cert_rpcapi.fetch_ca(context,
                                             project_id=context.project_id)
        except exception.CryptoCAFileNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())
        return {'certificate': _translate_certificate_view(cert)}

    @extensions.expected_errors(())
    @wsgi.response(201)
    def create(self, req, body=None):
        """Create a certificate."""
        context = req.environ['nova.context']
        authorize(context)
        pk, cert = self.cert_rpcapi.generate_x509_cert(context,
                user_id=context.user_id, project_id=context.project_id)
        context = req.environ['nova.context']
        return {'certificate': _translate_certificate_view(cert, pk)}


class Certificates(extensions.V3APIExtensionBase):
    """Certificates support."""

    name = "Certificates"
    alias = ALIAS
    version = 1

    def get_resources(self):
        resources = [
            extensions.ResourceExtension('os-certificates',
                                         CertificatesController(),
                                         member_actions={})]
        return resources

    def get_controller_extensions(self):
        return []
