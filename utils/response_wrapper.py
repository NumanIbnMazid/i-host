from rest_framework.response import Response


class ResponseWrapper(Response):

    def __init__(self, data=None, error_code=None, template_name=None, headers=None, exception=False, content_type=None,
                 msg=None, response_success=True, status=None, data_type=None):
        """
        Alters the init arguments slightly.
        For example, drop 'template_name', and instead use 'data'.

        Setting 'renderer' and 'media_type' will typically be deferred,
        For example being set automatically by the `APIView`.

        Parameters
        ----------
        data :
            [same as response], by default None
        error_code :
            [pass error code if error occurs ], by default None
        template_name :
            [same as response], by default None
        headers :
            [same as response], by default None
        exception : bool, optional
            [same as response], by default False
        content_type :
            [same as response], by default None
        error_msg :
            [pass error msg ], by default None
        response_success : bool, optional
            [if server able to handle req or not], by default True
        status :
            [status code if server is able to handle the req usually 200-299], by default None
        data_type :
            [description], by default None
        """

        if error_code is None and status is not None:
            if status > 299 or status < 200:
                error_code = status
                response_success = False
                if msg == None:
                    msg = "Failed"
            elif msg == None:
                msg = "Successful"
        if error_code is not None:
            response_success = False
            if msg == None:
                msg = "Failed"

        status_by_default_for_gz = 200

        output_data = {
            "data": data,
            "status": response_success,
            "msg": msg
        }
        if data_type is not None:
            output_data["type"] = data_type

        # status=200
        super().__init__(data=output_data, status=status_by_default_for_gz,
                         template_name=template_name, headers=headers, exception=exception, content_type=content_type)
