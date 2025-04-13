import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:

        app = adsk.core.Application.get()
        ui  = app.userInterface

        for i in range(ui.allToolbarPanels.count):
            if ui.allToolbarPanels.item(i).isVisible == True:
                print(ui.allToolbarPanels.item(i).id)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))