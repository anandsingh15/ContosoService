using FakeXrmEasy;
using FakeXrmEasy.Abstractions;
using FakeXrmEasy.Abstractions.Enums;
using FakeXrmEasy.Middleware;
using FakeXrmEasy.Middleware.Crud;
using FakeXrmEasy.Plugins;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Microsoft.Xrm.Sdk;
using System;
using System.Collections.Generic;

namespace ContosoService.Plugins.Tests
{
    [TestClass]
    public class MaintenanceJobCompletionPluginTests
    {
        private static readonly DateTime FixedUtcNow = new DateTime(2026, 8, 11, 14, 30, 0, DateTimeKind.Utc);

        [TestMethod]
        public void CreateRejectsPastScheduledDateUsingInjectedClock()
        {
            var target = Job();
            target["aks_scheduleddate"] = FixedUtcNow.Date.AddDays(-1);

            var exception = Assert.ThrowsException<InvalidPluginExecutionException>(
                () => new MaintenanceJobCompletionPlugin(() => FixedUtcNow).ValidateCreate(target));

            Assert.AreEqual("Scheduled date cannot be earlier than today.", exception.Message);
        }

        [TestMethod]
        public void CreateRejectsInitialCompletedStage()
        {
            var target = Job();
            target["aks_stage"] = Stage(MaintenanceJobCompletionPlugin.CompletedStage);

            var exception = Assert.ThrowsException<InvalidPluginExecutionException>(
                () => Execute("Create", target));

            Assert.AreEqual("A new maintenance job cannot be created as Completed.", exception.Message);
        }

        [TestMethod]
        public void UpdateCompletesRoadworthyVehicleWithPartAndSetsInjectedDate()
        {
            var vehicleId = Guid.NewGuid();
            var jobId = Guid.NewGuid();
            var context = Context(
                Vehicle(vehicleId, 74875, true),
                new Entity("aks_jobpart", Guid.NewGuid())
                {
                    ["aks_maintenancejobid"] = new EntityReference("aks_maintenancejob", jobId)
                });
            var target = Job(jobId);
            target["aks_stage"] = Stage(MaintenanceJobCompletionPlugin.CompletedStage);
            var preImage = Job(jobId);
            preImage["aks_stage"] = Stage(74878);
            preImage["aks_vehicleid"] = new EntityReference("aks_vehicle", vehicleId);

            new MaintenanceJobCompletionPlugin(() => FixedUtcNow).ValidateUpdate(
                target,
                preImage,
                jobId,
                context.GetOrganizationService());

            Assert.AreEqual(FixedUtcNow, target.GetAttributeValue<DateTime>("aks_completeddate"));
        }

        [TestMethod]
        public void UpdateRejectsCompletionWithoutParts()
        {
            var vehicleId = Guid.NewGuid();
            var context = Context(Vehicle(vehicleId, 74875, true));
            var target = Job();
            target["aks_stage"] = Stage(MaintenanceJobCompletionPlugin.CompletedStage);
            var preImage = Job(target.Id);
            preImage["aks_stage"] = Stage(74878);
            preImage["aks_vehicleid"] = new EntityReference("aks_vehicle", vehicleId);

            var exception = Assert.ThrowsException<InvalidPluginExecutionException>(
                () => Execute(context, "Update", target, preImage));

            Assert.AreEqual("Add at least one job part before completing the maintenance job.", exception.Message);
        }

        [TestMethod]
        public void UpdateRejectsRetiredVehicle()
        {
            AssertVehicleRejected(
                MaintenanceJobCompletionPlugin.RetiredVehicleStatus,
                true,
                "A maintenance job cannot be completed for a retired vehicle.");
        }

        [TestMethod]
        public void UpdateRejectsNonRoadworthyVehicle()
        {
            AssertVehicleRejected(
                74875,
                false,
                "The selected vehicle must be roadworthy before completing the maintenance job.");
        }

        [TestMethod]
        public void UpdateRejectsReopeningCompletedJob()
        {
            var target = Job();
            target["aks_stage"] = Stage(74878);
            var preImage = Job(target.Id);
            preImage["aks_stage"] = Stage(MaintenanceJobCompletionPlugin.CompletedStage);

            var exception = Assert.ThrowsException<InvalidPluginExecutionException>(
                () => Execute("Update", target, preImage));

            Assert.AreEqual("A completed maintenance job cannot be reopened.", exception.Message);
        }

        [TestMethod]
        public void UpdateWithUnchangedStageIsNoOp()
        {
            var target = Job();
            target["aks_stage"] = Stage(74878);
            var preImage = Job(target.Id);
            preImage["aks_stage"] = Stage(74878);

            Execute("Update", target, preImage);

            Assert.IsFalse(target.Contains("aks_completeddate"));
        }

        private static void AssertVehicleRejected(int status, bool roadworthy, string message)
        {
            var vehicleId = Guid.NewGuid();
            var context = Context(Vehicle(vehicleId, status, roadworthy));
            var target = Job();
            target["aks_stage"] = Stage(MaintenanceJobCompletionPlugin.CompletedStage);
            var preImage = Job(target.Id);
            preImage["aks_stage"] = Stage(74878);
            preImage["aks_vehicleid"] = new EntityReference("aks_vehicle", vehicleId);

            var exception = Assert.ThrowsException<InvalidPluginExecutionException>(
                () => Execute(context, "Update", target, preImage));

            Assert.AreEqual(message, exception.Message);
        }

        private static IXrmFakedContext Context(params Entity[] rows)
        {
            var context = MiddlewareBuilder
                .New()
                .AddCrud()
                .UseCrud()
                .SetLicense(FakeXrmEasyLicense.RPL_1_5)
                .Build();
            context.Initialize(new List<Entity>(rows));
            return context;
        }

        private static void Execute(string message, Entity target, Entity preImage = null)
        {
            Execute(Context(), message, target, preImage);
        }

        private static void Execute(IXrmFakedContext context, string message, Entity target, Entity preImage = null)
        {
            var pluginContext = context.GetDefaultPluginContext();
            pluginContext.MessageName = message;
            pluginContext.Stage = 20;
            pluginContext.Mode = 0;
            pluginContext.PrimaryEntityName = "aks_maintenancejob";
            pluginContext.PrimaryEntityId = target.Id;
            pluginContext.InputParameters = new ParameterCollection { ["Target"] = target };
            if (preImage != null)
            {
                pluginContext.PreEntityImages = new EntityImageCollection { ["PreImage"] = preImage };
            }

            context.ExecutePluginWith<MaintenanceJobCompletionPlugin>(pluginContext);
        }

        private static Entity Job(Guid? id = null)
        {
            return new Entity("aks_maintenancejob", id ?? Guid.NewGuid());
        }

        private static Entity Vehicle(Guid id, int status, bool roadworthy)
        {
            return new Entity("aks_vehicle", id)
            {
                ["aks_status"] = Stage(status),
                ["aks_roadworthy"] = roadworthy
            };
        }

        private static OptionSetValue Stage(int value)
        {
            return new OptionSetValue(value);
        }
    }
}