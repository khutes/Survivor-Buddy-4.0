"""
Unit tests for BuddyAudioClient
"""

import pytest
from pytest_mock import mocker
import time

from gui.BuddyAudioClient import BuddyAudioClient

class DefaultValues:
    """
    Default values to run tests with. Used for initializing BuddyAudioClient
    """
    ip = 'localhost'
    port = 8080

class ValueHolder:
    """
    Class to hold some dicitonaries used for test inputs
    """

    input_dicts = [

        {
            'index': 1, 
            'structVersion': 2, 
            'name': 'Microphone 1', 
            'hostApi': 0, 'maxInputChannels': 1, 
            'maxOutputChannels': 0, 
            'defaultLowInputLatency': 0.09,
            'defaultLowOutputLatency': 0.09, 
            'defaultHighInputLatency': 0.18, 
            'defaultHighOutputLatency': 0.18, 
            'defaultSampleRate': 44100.0
        },
        {
            'index': 0, 
            'structVersion': 2, 
            'name': 'Microsoft Sound Mapper - Input', 
            'hostApi': 0, 'maxInputChannels': 2, 
            'maxOutputChannels': 0,
            'defaultLowInputLatency': 0.09, 
            'defaultLowOutputLatency': 0.09, 
            'defaultHighInputLatency': 0.18, 
            'defaultHighOutputLatency': 0.18, 
            'defaultSampleRate': 44100.0
        },
        {
            'index': 5, 
            'structVersion': 2, 
            'name': 'Speaker', 
            'hostApi': 0, 'maxInputChannels': 0, 
            'maxOutputChannels': 2, 
            'defaultLowInputLatency': 0.09,
            'defaultLowOutputLatency': 0.09, 
            'defaultHighInputLatency': 0.18, 
            'defaultHighOutputLatency': 0.18, 
            'defaultSampleRate': 44100.0
         }
    ]

    output_only = [input_dicts[2]]  #slice representing output only devices
    input_only = input_dicts[0:2]   #slice representing input only devices

    input_indicies = [0,1]  #list of input device indicies
    output_indicies = 2     #output device indicies, currently only 1

    def getDict(self, index):
        """
        Gets dictionary from a given index in self.input_dicts

        :param index: index of wanted dict
        :type index: int
        :return: the dictionary at the index of self.input_dicts
        :rtype: dict
        """
        return self.input_dicts[index]

def getNames(in_list):
    """
    Helper funtion for testing getDeviceNames() function. Gets the value of the name
    key from each dict

    :param in_list: the list of dictionaries to pull names from
    :type in_list: list[dict]
    :return:list of values from "name" keyword if input dicts
    :rtype: list[String]
    """
    name_list = []
    for d in in_list:
        name_list.append(d['name'])
    return name_list

def getIndexFromName(in_list, name):
    """
    Helper function for testing setInputDevice() function. Retunrns the index of
    the entered name if found. None otherwise

    :param in_list: the list of dictionaries to check
    :type in_list: list[dict]
    :param name: the name to search for in each dict of in_list
    :type name: String
    :return: the value of the index keyword in the dict which contains the given name value
    :rtype: int or None

    """
    for d in in_list:
        if d['name'] == name:
            return d['index']
    return None




class TestBuddyAudioClientHappy:
    """
    Suite of Happy Path tests for BuddyAudioClient
    """

    def test_connect_successful(self, mocker):
        """
        Tests that the connect methos returns True when 
        it successfully connects and that it sends the chunk size
        to the server
        """
        
        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_socket = mocker.patch('socket.socket', autospec=True)

        #run
        return_connect = bac._connect()

        #check
        mock_socket.return_value.connect.assert_called_with(
            (DefaultValues.ip, DefaultValues.port)
        )
        mock_socket.return_value.sendall.assert_called_with(
            str(BuddyAudioClient.default_chunk_size).encode('utf-8')
        )
        assert return_connect == True


    @pytest.mark.parametrize("input_val", [bytes((1,2,3)), bytes(0), bytearray([2]*1024)])
    def test_stream_loop(self, mocker, input_val):
        """
        Tests that the bytes are properly read/decoded and sent unmodified to the socket
        """

        read_val = input_val

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_socket = mocker.patch('socket.socket', autospec=True)
        mock_socket.return_value._closed = False
        bac.client_socket = mock_socket.return_value

        mock_pyaudio_stream = mocker.patch('pyaudio.Stream', autospec=True)
        mock_pyaudio_stream.return_value.read.return_value = read_val
        bac.audio_stream = mock_pyaudio_stream.return_value
    
        bac.continue_stream = True

        #run
        bac.streamLoop()

        #check
        mock_pyaudio_stream.return_value.read.assert_called_with(BuddyAudioClient.default_chunk_size)
        mock_socket.return_value.sendall.assert_called_with(read_val)
        assert bac.continue_stream == True

    @pytest.mark.parametrize('input_val', ValueHolder.input_only)
    def test_get_input_device_dicts_input_devices(self, mocker, input_val):
        """
        Tests that getInputDeviceDicts properly filters and returns only input devices
        """

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_pyaudio = mocker.patch('pyaudio.PyAudio', autospec=True)
        mock_pyaudio.get_device_info_by_host_api_device_index.return_value = input_val

        bac.audio_handler = mock_pyaudio
        bac.current_device_dict['deviceCount'] = 1
        bac.audio_handler.get_default_host_api_info()['index'] = 0

        #run
        rdict = bac.getInputDeviceDicts()

        #check
        mock_pyaudio.get_device_info_by_host_api_device_index.assert_called()
        assert len(rdict) == 1

    @pytest.mark.parametrize('input_val', ValueHolder.output_only)
    def test_get_input_device_dicts_output_devices(self, mocker, input_val):
        '''
        Tests that getInputDeviceDicts properly filters for input devices. This
        test gives only output devices as input so it will return 0 dicts
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_pyaudio = mocker.patch('pyaudio.PyAudio', autospec=True)
        mock_pyaudio.get_device_info_by_host_api_device_index.return_value = input_val

        bac.audio_handler = mock_pyaudio
        bac.current_device_dict['deviceCount'] = 1
        bac.audio_handler.get_default_host_api_info()['index'] = 0

        #run
        rdict = bac.getInputDeviceDicts()

        #check
        mock_pyaudio.get_device_info_by_host_api_device_index.assert_called()
        assert len(rdict) == 0

    def test_get_input_device_names_number_of_names(self, mocker):
        '''
        Tests that getInputDeviceNames() returns a list of the device names and
        that the number of names in the list is as expected
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_getInputDeviceDicts = mocker.patch.object(BuddyAudioClient, 'getInputDeviceDicts')
        mock_getInputDeviceDicts.return_value = ValueHolder.input_dicts

        #run
        rlist = bac.getInputDeviceNames()

        #check
        assert len(rlist) == len(ValueHolder.input_dicts)

    def test_get_input_device_name_content(self, mocker):
        '''
        Tests that getInputDeviceNames() returns a list of the device names.
        This test checks that the names are all the expected ones
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_getInputDeviceDicts = mocker.patch.object(BuddyAudioClient, 'getInputDeviceDicts')
        mock_getInputDeviceDicts.return_value = ValueHolder.input_dicts

        #run
        rlist = bac.getInputDeviceNames()

        #check
        names_good = True
        for i, name in enumerate(rlist):
            if(name != ValueHolder.input_dicts[i]['name']):
                names_good = False
                break
        assert names_good

    @pytest.mark.parametrize("input_vals", getNames(ValueHolder.input_dicts))
    def test_set_input_device(self, mocker, input_vals):
        '''
        Tests that setInputDevice properly sets the input device to the input
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_getInputDeviceDicts = mocker.patch.object(BuddyAudioClient, 'getInputDeviceDicts')
        mock_getInputDeviceDicts.return_value = ValueHolder.input_dicts

        bac.input_device_index = None

        #run
        bac.setInputDevice(input_vals)

        #check
        assert bac.input_device_index == getIndexFromName(ValueHolder.input_dicts, input_vals)

    def test_handle_connect_connection_success(self, mocker):
        '''
        Test that the handleConnectAndStart() method calls start_strem when connection is successful
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mocker.patch('socket.socket', autospec=True)
        mock_connect = mocker.patch.object(BuddyAudioClient, '_connect')
        mock_connect.return_value = True

        #run
        bac.connect()

        #check
        mock_connect.assert_called()

    def test_handle_connect_and_start_connection_failed(self, mocker):
        '''
        Test that the handleConnectAndStart() method calls start_strem when connection fails
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mocker.patch('socket.socket', autospec=True)
        mock_connect = mocker.patch.object(BuddyAudioClient, '_connect')
        mock_connect.return_value = False

        #run
        bac.connect()

        #check
        mock_connect.assert_called()

    def test_disconnect(self, mocker):
        '''
        Tests disconnectAndStop() method if called when connected
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_socket = mocker.patch('socket.socket', autospec=True)

        bac.client_socket = mock_socket
        bac.continue_stream = True

        #run
        bac.disconnect()

        #check
        assert bac.client_socket is None
        assert bac.is_connected == False
        mock_socket.close.assert_called()


class TestBuddyAudioClientNegative:

    def test_connect_timeout(self, mocker):
        '''
        Tests that the connect method handles a TimeoutError from
        socket.connect()
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_socket = mocker.patch('socket.socket', autospec=True)
        mock_socket.return_value.connect.side_effect = TimeoutError

        #run
        return_connect = bac._connect()

        #check
        assert return_connect == False

    def test_connect_connection_refused(self, mocker):
        '''
        Tests that the connect method handles a timeout error from
        socket.connect()
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_socket = mocker.patch('socket.socket', autospec=True)
        mock_socket.return_value.connect.side_effect = ConnectionRefusedError

        #run
        return_connect = bac._connect()

        #check
        assert return_connect == False
    
    @pytest.mark.parametrize("input_vals", getNames(ValueHolder.input_dicts))
    def test_set_input_device_no_devices_present(self, mocker, input_vals):
        '''
        Tests that setInputDevice handles the case when no devices are detected
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_getInputDeviceDicts = mocker.patch.object(BuddyAudioClient, 'getInputDeviceDicts')
        mock_getInputDeviceDicts.return_value = []
        
        bac.input_device_index = None

        #run
        bac.setInputDevice(input_vals)

        #check
        assert bac.input_device_index == None

    def test_set_input_device_name_not_found(self, mocker):
        '''
        Tests that setInputDevice handles the case when no devices are detected
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_getInputDeviceDicts = mocker.patch.object(BuddyAudioClient, 'getInputDeviceDicts')
        mock_getInputDeviceDicts.return_value = ValueHolder.input_dicts

        bac.input_device_index = None

        #run
        bac.setInputDevice('fake name')

        #check
        assert bac.input_device_index == None

    def test_disconnect(self, mocker):
        '''
        Tests disconnectAndStop() method if called when NOT connected
        '''

        #setup
        bac = BuddyAudioClient(DefaultValues.ip, DefaultValues.port)
        mock_socket = mocker.patch('socket.socket', autospec=True)

        bac.client_socket = None

        #run
        bac.disconnect()

        #check
        assert bac.client_socket is None
        mock_socket.close.assert_not_called()
    
