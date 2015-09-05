
import time
from direct.stdpy.file import open

from Util.DebugObject import DebugObject
from Util.FunctionDecorators import protected

from RenderStage import RenderStage
from Stages.EarlyZStage import EarlyZStage
from Stages.FlagUsedCellsStage import FlagUsedCellsStage
from Stages.CollectUsedCellsStage import CollectUsedCellsStage
from Stages.CullLightsStage import CullLightsStage

from GUI.PipeViewer import PipeViewer

class StageManager(DebugObject):

    # This defines the order of all stages, in case they are attached
    stageOrder = [
        EarlyZStage,
        FlagUsedCellsStage,
        CollectUsedCellsStage,
        CullLightsStage
    ]

    """ This manager takes a list of RenderStages and puts them into an order,
    and also connects the different pipes """

    def __init__(self, pipeline):
        """ Constructs the stage manager """
        DebugObject.__init__(self, "StageManager")
        self.stages = []
        self.inputs = {}
        self.pipes = {}
        self.ubos = {}
        self.defines = {}
        self.pipeline = pipeline

        # Register the manager so the pipe viewer can read our data
        PipeViewer.registerStageMgr(self)

    def addStage(self, stage):
        """ Adds a new stage """

        if stage.__class__ not in self.stageOrder:
            self.error("They stage type '" + stage.getName() + "' is not registered yet!")
            return

        self.stages.append(stage)

    def define(self, key, value):
        """ Registers a new define for the shader auto config """
        self.defines[key] = value

    def setup(self):
        """ Setups the stages """
        self.debug("Setup stages ...")

        # Sort stages
        self.stages.sort(key = lambda stage: self.stageOrder.index(stage.__class__))

        # Process each stage
        for stage in self.stages:
            self.debug("Creating stage", stage.__class__)


            # Create the pass
            stage.create()

            # Check if all pipes are available, and set them
            for pipe in stage.getInputPipes():
                if pipe not in self.pipes:
                    self.error("Pipe '" + pipe + "' is missing for", stage)
                    continue

                stage.setShaderInput(pipe, self.pipes[pipe])

            # Check if all inputs are available, and set them
            for inputBinding, inputSrc in stage.getRequiredInputs().iteritems():
                if inputSrc not in self.inputs and inputSrc not in self.ubos:
                    self.error("Input '" + inputSrc + "' is missing for", stage)
                    continue

                if inputSrc in self.inputs:
                    stage.setShaderInput(inputBinding, self.inputs[inputSrc])
                else:
                    ubo = self.ubos[inputSrc]
                    ubo.bindTo(stage)


            # Register all the new pipes, inputs and defines
            for pipeName, pipeData in stage.getProducedPipes().iteritems():
                self.pipes[pipeName] = pipeData

            for defineName, defineData in stage.getProducedDefines().iteritems():
                if defineName in self.defines:
                    self.warn("Stage",stage,"overrides define",defineName)
                self.defines[defineName] = defineData

            for inputName, inputData in stage.getProducedInputs().iteritems():
                if inputName in self.inputs:
                    self.warn("Stage",stage,"overrides input", inputName)
                self.inputs[inputName] = inputData

    def setShaders(self):
        """ This pass sets the shaders to all passes and also generates the
        shader auto config"""

        # First genereate the auto config
        self._writeAutoconfig()

        # Then generate the shaders
        for stage in self.stages:
            stage.setShaders()

    def updateStages(self):
        """ Calls the update method for each stage """
        for stage in self.stages:
            stage.update()
            
    @protected
    def _writeAutoconfig(self):
        """ Writes the shader auto config, based on the defines specified by the
        different stages """

        self.debug("Writing shader autoconfig")

        # Generate autoconfig as string
        output = "#pragma once\n\n"
        output += "// Autogenerated by RenderingPipeline\n"
        output += "// Do not edit! Your changes will be lost.\n\n"

        for key, value in sorted(self.defines.iteritems()):
            output += "#define " + key + " " + str(value) + "\n"

        output += "#define RANDOM_TIMESTAMP " + str(time.time()) + "\n"

        # Try to write the file
        try:
            with open("$$PipelineTemp/ShaderAutoConfig.include", "w") as handle:
                handle.write(output)
        except Exception, msg:
            self.error("Error writing shader autoconfig. Maybe no write-access?")
            return

