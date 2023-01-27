import autodocsumm


def setup(app):
    for cls in (autodocsumm.AutoSummClassDocumenter, autodocsumm.AutoSummModuleDocumenter,
                autodocsumm.CallableAttributeDocumenter, autodocsumm.NoDataDataDocumenter,
                autodocsumm.NoDataAttributeDocumenter):
        cls.priority -= 1
        app.add_autodocumenter(cls, override=True)
