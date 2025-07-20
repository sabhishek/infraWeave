"""Dispatch utility mapping resource categories to job handler classes."""
from __future__ import annotations

from importlib import import_module
from typing import Type

from .jobs.base import BaseJobHandler
from .models import ResourceCategory

# Explicit mapping. Dynamically import to avoid circular deps.
_RESOURCE_TO_HANDLER: dict[str, str] = {
    ResourceCategory.compute_osimages.value: "jobs.compute.osimages.ComputeOSImagesJobHandler",
    ResourceCategory.compute_vms.value: "jobs.compute.vms.ComputeVMsJobHandler",
    ResourceCategory.k8s_namespace.value: "jobs.k8s.namespace.K8sNamespaceJobHandler",
    ResourceCategory.k8s_pvs.value: "jobs.k8s.pvs.K8sPVsJobHandler",
    ResourceCategory.k8s_service_mesh.value: "jobs.k8s.service_mesh.K8sServiceMeshJobHandler",
    ResourceCategory.enterprise_networking_lb.value: "jobs.enterprise_networking.lb.EnterpriseNetworkingLBHandler",
    ResourceCategory.enterprise_networking_cname.value: "jobs.enterprise_networking.cname.EnterpriseNetworkingCNAMEHandler",
    ResourceCategory.enterprise_networking_fw.value: "jobs.enterprise_networking.fw.EnterpriseNetworkingFWHandler",
    ResourceCategory.storage_s3tenant.value: "jobs.storage.s3tenant.StorageS3TenantHandler",
    ResourceCategory.storage_s3bucket.value: "jobs.storage.s3bucket.StorageS3BucketHandler",
    ResourceCategory.misc.value: "jobs.misc.MiscJobHandler",
}


def get_handler_class(category: str) -> Type[BaseJobHandler]:  # noqa: D401
    """Return the handler class for *category*. Raises KeyError if unknown."""
    dotted_path = _RESOURCE_TO_HANDLER[category]
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = import_module(f". {module_path}", package=__name__.split(".")[0])
    return getattr(module, class_name)  # type: ignore[return-value]
