from configparser import ConfigParser


def parse_config(path: str):
    """

    Args:
        path (str): path to .ini file

    Returns:
        Path to WCDTool executable, Relative path from WCDTool executable to testcase folder
    """
    wcdtool_path = 'E:\\Thesis_WCDTool\\'
    wcdtool_testcase_subpath = 'usecases\\generated\\'

    config = ConfigParser()
    config.read(path)

    try:
        wcdtool_path = config["wcdtool"]["path"]
        wcdtool_testcase_subpath = config["wcdtool"]["testcase_subpath"]
    except KeyError:
        pass

    return wcdtool_path, wcdtool_testcase_subpath
