import adsk.core
import adsk.fusion
import traceback
import os
import time

app = None
ui = None
handlers = []

HARDCODED_PART_PATH = r"/Users/nicolema/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/TipTop/models/Blade.f3d"

class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            cmd = args.command
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            
            selInput = cmd.commandInputs.addSelectionInput('selection', 'Select Part', 'Select a part to replace')
            selInput.addSelectionFilter('Occurrences')
            selInput.setSelectionLimits(1, 1)
        except:
            ui.messageBox(f'Error in CommandCreatedHandler:\n{traceback.format_exc()}')

def runSimulatedOptimization():
    try:
        optimization_steps = [
            "Initializing topology optimization...",
            "Running our PEN Algorithm",
            "Refining mesh density...",
            "Validating design parameters...",
            "Finalizing optimized geometry..."
        ]
        
        steps_count = len(optimization_steps)
        progressDialog = ui.createProgressDialog()
        progressDialog.isCancelButtonShown = True
        progressDialog.show('Topological Optimization', 
                           optimization_steps[0], 
                           0, 
                           100)
        
        for i, step in enumerate(optimization_steps):
            if progressDialog.wasCancelled:
                return False

            progress_value = int((i / steps_count) * 100)
            progressDialog.message = step
            progressDialog.progressValue = progress_value
            
            increment = 100 // steps_count // 10  
            for j in range(10):
                if progressDialog.wasCancelled:
                    return False
                time.sleep(0.1)  
                current_progress = progress_value + (j * increment // 10)
                progressDialog.progressValue = min(current_progress, 99) 
            
        progressDialog.progressValue = 99
        progressDialog.message = "Optimization complete!"
        time.sleep(0.5)
        
        progressDialog.hide()
        return True
    except:
        ui.messageBox(f'Error in progress dialog:\n{traceback.format_exc()}')
        return False

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            selInput = inputs.itemById('selection')
            
            if selInput.selectionCount == 0:
                ui.messageBox('No part selected')
                return
                
            if not os.path.exists(HARDCODED_PART_PATH):
                ui.messageBox(f'F3D file not found at: {HARDCODED_PART_PATH}\nPlease update the HARDCODED_PART_PATH variable.')
                return
                
            selectedOcc = selInput.selection(0).entity
            transform = selectedOcc.transform
            
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
            if not design:
                ui.messageBox('The active product is not a design')
                return
            
            success = runSimulatedOptimization()
            
            if not success:
                return
                
            try:
                finalProgress = ui.createProgressDialog()
                finalProgress.isCancelButtonShown = True
                finalProgress.show('Applying Optimization', 
                                  'Applying optimized design...', 
                                  0, 
                                  100)
                
                selectedOcc.deleteMe()
                finalProgress.progressValue = 30
                time.sleep(0.3)
                
                importManager = app.importManager
                importOptions = importManager.createFusionArchiveImportOptions(HARDCODED_PART_PATH)
                rootComp = design.rootComponent
                finalProgress.progressValue = 60
                time.sleep(0.3)
                
                newComponent = importManager.importToTarget(importOptions, rootComp)
                finalProgress.progressValue = 80
                time.sleep(0.3)
                
                for occ in rootComp.occurrences:
                    if occ.component == newComponent:
                        occ.transform = transform
                        break
                
                finalProgress.progressValue = 100
                finalProgress.message = "Optimization applied successfully!"
                time.sleep(0.5)
                
                finalProgress.hide()
                
                ui.messageBox('Topological optimization complete!\nPart successfully optimized and replaced.')
                
            except Exception as e:
                ui.messageBox(f'Error during replacement: {str(e)}\n{traceback.format_exc()}')
                
        except Exception as e:
            ui.messageBox(f'Error in CommandExecuteHandler: {str(e)}\n{traceback.format_exc()}')

def addButtonToPanel():
    try:
        cmdDef = ui.commandDefinitions.itemById('replacerCmdId')
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(
                'replacerCmdId', 
                'TipTop: Optimize Part', 
                'Run topological optimization on selected part', 
                ''
            )
        
        cmdCreatedHandler = CommandCreatedHandler()
        cmdDef.commandCreated.add(cmdCreatedHandler)
        handlers.append(cmdCreatedHandler)
        
        designWS = ui.workspaces.itemById('FusionSolidEnvironment')
        if not designWS:
            ui.messageBox('FusionSolidEnvironment workspace not found')
            return None
            
        modifyPanel = designWS.toolbarPanels.itemById('SolidModifyPanel')
        if not modifyPanel:
            ui.messageBox('SolidModifyPanel not found')
            return None
        
        buttonControl = modifyPanel.controls.itemById('replacerCmdId')
        if not buttonControl:
            buttonControl = modifyPanel.controls.addCommand(cmdDef)
            buttonControl.isVisible = True
        
        return cmdDef
    except:
        ui.messageBox(f'Error adding button to panel:\n{traceback.format_exc()}')
        return None

def run(context):
    try:
        global app, ui
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        cmdDef = addButtonToPanel()
        
        if cmdDef:
            ui.messageBox('Topological Optimization Add-in loaded successfully.\nLook for "Optimize Part" button in Modify panel.')
        
    except:
        if ui:
            ui.messageBox(f'Failed to start add-in:\n{traceback.format_exc()}')

def stop(context):
    try:
        cmdDef = ui.commandDefinitions.itemById('replacerCmdId')
        if cmdDef:
            cmdDef.deleteMe()
            
        panel = ui.allToolbarPanels.itemById('SolidModifyPanel')
        if panel:
            btn = panel.controls.itemById('replacerCmdId')
            if btn:
                btn.deleteMe()
                
        ui.messageBox('Topological Optimization Add-in unloaded.')
        
    except:
        if ui:
            ui.messageBox(f'Error cleaning up add-in:\n{traceback.format_exc()}')