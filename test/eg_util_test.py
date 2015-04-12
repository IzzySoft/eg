import os
import subprocess

from eg import eg_config
from eg import eg_util
from mock import Mock
from mock import patch
from nose.tools import assert_equal


def test_pager_set_returns_true():
    with patch('os.getenv', return_value='less'):
        actual = eg_util.pager_env_is_set()
        assert actual is True


def test_pager_not_set_returns_false():
    # os.getenv returns None if a variable is not set
    with patch('os.getenv', return_value=None):
        actual = eg_util.pager_env_is_set()
        assert actual is False


def test_open_pager_to_line_number_invokes_correctly_for_less():
    pager = 'less'
    file_path = 'examples/touch.md'
    with patch('subprocess.call') as mock_method:
        eg_util.open_pager_for_file(pager, file_path)
        mock_method.assert_called_once_with([pager, file_path])


def test_get_pager_with_custom_correct():
    custom_pager = 'more'
    with patch('eg.eg_util.pager_env_is_set', return_value=True):
        with patch('os.getenv', return_value=custom_pager):
            assert eg_util.get_pager() == custom_pager


def test_get_pager_without_custom_correct():
    with patch('eg.eg_util.pager_env_is_set', return_value=False):
        assert_equal(eg_util.get_pager(), eg_util.DEFAULT_PAGER)


def test_get_file_path_for_program_correct():
    program = 'cp'
    examples_dir = '/Users/tyrion/test/eg_dir'
    program_file = program + eg_util.EXAMPLE_FILE_SUFFIX
    target = os.path.join(examples_dir, program_file)

    actual = eg_util.get_file_path_for_program(program, examples_dir)

    assert_equal(actual, target)


def test_has_default_entry_for_program_no_examples_dir():
    config = eg_config.Config(
        examples_dir=None,
        custom_dir='customdir',
        color_config=None,
        use_color=False
    )

    program = 'cp'

    has_entry = eg_util.has_default_entry_for_program(program, config)

    assert_equal(False, has_entry)


def test_has_custom_entry_for_program_no_custom_dir():
    config = eg_config.Config(
        examples_dir='examplesdir',
        custom_dir=None,
        color_config=None,
        use_color=False
    )

    program = 'find'

    has_entry = eg_util.has_custom_entry_for_program(program, config)

    assert_equal(False, has_entry)


def test_has_default_entry_when_present():
    config = eg_config.Config(
        examples_dir='examplesdir',
        custom_dir=None,
        color_config=None,
        use_color=False,
    )
    program = 'mv'

    path = '/Users/tyrion/examplesdir/mv.md'

    _helper_assert_path_isfile_not_present(
        config,
        program,
        path,
        'default',
        True,
        True
    )


def test_has_default_entry_when_not_present():
    config = eg_config.Config(
        examples_dir='examplesdir',
        custom_dir=None,
        color_config=None,
        use_color=False
    )
    program = 'cp'

    path = '/Users/tyrion/examplesdir/cp.md'

    _helper_assert_path_isfile_not_present(
        config,
        program,
        path,
        'default',
        False,
        False,
    )


def test_has_custom_entry_when_present():
    config = eg_config.Config(
        examples_dir=None,
        custom_dir='customdir',
        color_config=None,
        use_color=False
    )
    program = 'find'

    path = '/Users/tyrion/customdir/find.md'

    _helper_assert_path_isfile_not_present(
        config,
        program,
        path,
        'custom',
        True,
        True
    )


def test_has_custom_entry_when_not_present():
    config = eg_config.Config(
        examples_dir=None,
        custom_dir='customdir',
        color_config=None,
        use_color=False
    )

    program = 'locate'

    path = '/Users/tyrion/customdir/locate.md'

    _helper_assert_path_isfile_not_present(
        config,
        program,
        path,
        'custom',
        False,
        False,
    )


def _helper_assert_path_isfile_not_present(
        config,
        program,
        file_path_for_program,
        defaultOrCustom,
        isfile,
        has_entry):
    """
    Helper for asserting whether or not a default file is present. Pass in the
    parameters defining the program and directories and say whether or not that
    file should be found.
    """
    if defaultOrCustom != 'default' and defaultOrCustom != 'custom':
        raise TypeError(
            'defaultOrCustom must be default or custom, not ' + defaultOrCustom
        )
    with patch(
        'eg.eg_util.get_file_path_for_program',
        return_value=file_path_for_program
    ) as mock_get_path:
        with patch('os.path.isfile', return_value=isfile) as mock_isfile:

            actual = None
            correct_dir = None

            if (defaultOrCustom == 'default'):
                correct_dir = config.examples_dir
                actual = eg_util.has_default_entry_for_program(program, config)
            else:
                correct_dir = config.custom_dir
                actual = eg_util.has_custom_entry_for_program(program, config)

            mock_get_path.assert_called_once_with(program, correct_dir)
            mock_isfile.assert_called_once_with(file_path_for_program)

            assert_equal(actual, has_entry)


def test_handle_program_no_entries():
    program = 'cp'
    config = eg_config.Config(
        examples_dir=None,
        custom_dir=None,
        color_config=None,
        use_color=False
    )

    with patch(
        'eg.eg_util.has_default_entry_for_program',
        return_value=False
    ) as mock_has_default:
        with patch(
            'eg.eg_util.has_custom_entry_for_program',
            return_value=False
        ) as mock_has_custom:
            with patch(
                'eg.eg_util.open_pager_for_file'
            ) as mock_open_pager:
                eg_util.handle_program(program, config)

                mock_has_default.assert_called_once_with(program, config)
                mock_has_custom.assert_called_once_with(program, config)

                assert_equal(mock_open_pager.call_count, 0)


def test_handle_program_finds_paths_and_calls_open_pager():
    program = 'mv'
    pager = 'more'

    examples_dir = 'test-eg-dir'
    custom_dir = 'test-custom-dir'

    config = eg_config.Config(
        examples_dir=examples_dir,
        custom_dir=custom_dir,
        color_config=None,
        use_color=False
    )

    default_path = 'test-eg-dir/mv.md'
    custom_path = 'test-custom-dir/mv.md'

    def return_correct_path(*args, **kwargs):
        program_param = args[0]
        dir_param = args[1]
        if program_param != program:
            raise NameError('expected ' + program + ', got ' + program_param)
        if dir_param == examples_dir:
            return default_path
        elif dir_param == custom_dir:
            return custom_path
        else:
            raise NameError(
                'got ' +
                dir_param +
                ', expected ' +
                examples_dir +
                ' or ' +
                custom_dir)

    with patch(
        'eg.eg_util.has_default_entry_for_program',
        return_value=True
    ) as mock_has_default:
        with patch(
            'eg.eg_util.has_custom_entry_for_program',
            return_value=True
        ) as mock_has_custom:
            with patch(
                'eg.eg_util.open_pager_for_file'
            ) as mock_open_pager:
                with patch(
                    'eg.eg_util.get_file_path_for_program',
                    side_effect=return_correct_path
                ) as mock_get_file:
                    with patch('eg.eg_util.get_pager', return_value=pager):
                        eg_util.handle_program(program, config)

                        mock_has_default.assert_called_once_with(
                            program,
                            config
                        )
                        mock_has_custom.assert_called_once_with(
                            program,
                            config
                        )

                        mock_get_file.assert_any_call(
                            program,
                            examples_dir
                        )
                        mock_get_file.assert_any_call(
                            program,
                            custom_dir
                        )

                        mock_open_pager.assert_called_once_with(
                            pager,
                            default_file_path=default_path,
                            custom_file_path=custom_path
                        )


def test_open_pager_for_file_only_default():
    pager = 'more'
    default_path = 'test/default/path'
    with patch('subprocess.call') as mock_call:
        eg_util.open_pager_for_file(pager, default_path, None)

        mock_call.assert_called_once_with([pager, default_path])


def test_open_pager_for_file_only_custom():
    pager = 'more'
    custom_path = 'test/custom/path'
    with patch('subprocess.call') as mock_call:
        eg_util.open_pager_for_file(pager, None, custom_path)

        mock_call.assert_called_once_with([pager, custom_path])


def test_open_pager_for_both_file_types():
    # This is kind of a messy function, as we do a lot of messing around with
    # subprocess.Popen. We're not going to test that absolutely everything is
    # plugged in correctly, just that things are more or less right
    pager = 'less'
    default_path = 'test/default/path'
    custom_path = 'test/custom/path'
    cat = Mock(autospec=True)
    with patch('subprocess.Popen', return_value=cat) as mock_popen:
        with patch('subprocess.call') as mock_call:
            eg_util.open_pager_for_file(pager, default_path, custom_path)

            mock_popen.assert_called_once_with(
                ('cat', custom_path, default_path),
                stdout=subprocess.PIPE
            )

            mock_call.assert_called_once_with((pager), stdin=cat.stdout)


def test_list_supported_programs_only_default():
    example_dir = 'example/dir'
    custom_dir = 'custom/dir'

    config = eg_config.Config(
        examples_dir=example_dir,
        custom_dir=custom_dir,
        color_config=None,
        use_color=False
    )

    def give_list(*args, **kwargs):
        if args[0] == example_dir:
            return ['cp.md', 'find.md', 'xargs.md']
        else:
            return []

    with patch('os.path.isdir', return_value=True):
        with patch('os.listdir', side_effect=give_list):
            actual = eg_util.get_list_of_all_supported_commands(config)
            target = ['cp', 'find', 'xargs']

            assert_equal(actual, target)


def test_list_supported_programs_only_custom():
    example_dir = 'example/dir'
    custom_dir = 'custom/dir'

    config = eg_config.Config(
        examples_dir=example_dir,
        custom_dir=custom_dir,
        color_config=None,
        use_color=False
    )

    def give_list(*args, **kwargs):
        if args[0] == custom_dir:
            return ['awk.md', 'bar.md', 'xor.md']
        else:
            return []

    with patch('os.path.isdir', return_value=True):
        with patch('os.listdir', side_effect=give_list):
            actual = eg_util.get_list_of_all_supported_commands(config)
            target = ['awk +', 'bar +', 'xor +']

            assert_equal(actual, target)


def test_list_supported_programs_both():
    examples_dir = 'example/dir'
    custom_dir = 'custom/dir'

    config = eg_config.Config(
        examples_dir=examples_dir,
        custom_dir=custom_dir,
        color_config=None,
        use_color=False
    )

    def give_list(*args, **kwargs):
        if args[0] == examples_dir:
            return ['alpha', 'bar.md', 'both.md', 'examples']
        else:
            # custom_dir
            return ['azy.md', 'both.md', 'examples', 'zeta']

    with patch('os.path.isdir', return_value=True):
        with patch('os.listdir', side_effect=give_list):
            actual = eg_util.get_list_of_all_supported_commands(config)

            target = [
                'alpha',
                'azy +',
                'bar',
                'both *',
                'examples *',
                'zeta +'
            ]

            assert_equal(actual, target)


def test_list_supported_programs_fails_gracefully_if_no_dirs():
    config = eg_config.Config(None, None, None, None)

    actual = eg_util.get_list_of_all_supported_commands(config)
    target = []

    assert_equal(actual, target)


def test_calls_colorize_is_use_color_set():
    """We should call the colorize function if use_color = True."""
    assert_equal(True, False)


def test_does_not_call_colorize_if_use_color_false():
    """We should not call colorize if use_color = False."""
    assert_equal(True, False)
