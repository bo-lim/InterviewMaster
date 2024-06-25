'use client';
import React, { useEffect, useState } from "react";
import { checkAudioCodecPlaybackSupport, useRecordWebcam } from 'react-record-webcam';
import { PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { AudioRecorder,useAudioRecorder } from 'react-audio-voice-recorder';
import { PollyClient,SynthesizeSpeechCommand } from "@aws-sdk/client-polly";
import axios from "axios";
import ReactPlayer from 'react-player'
import { Cookies } from "react-cookie";
import { useRouter } from 'next/navigation'; // next/navigation에서 useRouter를 가져옴
import { create_polly, post_chat, post_new_qs, post_stt, save_audio, save_video } from "../api";


const Interview = () => {
  const cookies = new Cookies();
  const [start, setStart] = useState(0);
  const [question,setQuestion] = useState(cookies.get('simul_info'));
  const [frontQ, setFrontQ] = useState(cookies.get('simul_ques'));
  const [textPath, setTextPath] = useState("");
  const [chatQ, setchatQ] = useState("");
  const router = useRouter()
  const [count, setCount] = useState(1);

  const [loadingMessage, setLoadingMessage] = useState(""); // 로딩 메시지 상태 추가
  const [nextloadingMessage, setNextLoadingMessage] = useState(""); // 로딩 메시지 상태 추가

  const {
    activeRecordings,
    createRecording,
    cancelRecording,
    clearError,
    clearPreview,
    closeCamera,
    download,
    errorMessage,
    openCamera,
    pauseRecording,
    resumeRecording,
    startRecording,
    stopRecording,
  } = useRecordWebcam();

  // const client = new S3Client({
  //   region: 'ap-northeast-2',
  //   credentials: {
  //     accessKeyId: process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID,
  //     secretAccessKey: process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY,
  //   },
  // });
  // const polly_client = new PollyClient({
  //   region: 'ap-northeast-2',
  //   credentials: {
  //     accessKeyId: process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID,
  //     secretAccessKey: process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY,
  //   },
  // });


  const [audio_key,setAudio_key] = useState('audio/tmp.mp3');
  const [video_key,setVideo_key] = useState('video/tmp.webm');
  const recorderControls = useAudioRecorder();
  const addAudioElement = async (blob) => {
    const audio_formData = new FormData()
    audio_formData.append('audio_key',audio_key)
    audio_formData.append('blob',blob)
    save_audio(audio_formData)
    // const command = new PutObjectCommand({
    //   Key: audio_key,
    //   Body: blob,
    //   Bucket: bucket,
    // });

    // try {
    //   const response = client.send(command);
    //   console.log(response);
    // } catch (err) {
    //   console.error(err);
    // }
  };
  const polly = async (text) => {
    const arrayBuffer = await create_polly(text);
    const blob = new Blob([new Uint8Array(arrayBuffer)], { type: 'audio/mp3' });
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    audio.play();
  }
  // const polly = (text) => {
  //   const params = {
  //     "OutputFormat": "mp3",
  //     "Text": text,
  //     "TextType": "text",
  //     "VoiceId": "Seoyeon"
  //   };
  //   const command = new SynthesizeSpeechCommand(params);
  //   try{
  //     polly_client.send(command)
  //     .then(async (data) => {
  //       // Convert the ArrayBuffer to a Blob
  //       const arrayBuffer = await data.AudioStream.transformToByteArray();
  //       const blob = new Blob([arrayBuffer], { type: 'audio/mp3' });

  //       // Create a URL for the Blob and play the audio
  //       const audioUrl = URL.createObjectURL(blob);
  //       const audio = new Audio(audioUrl);
  //       audio.play();
  //     })
  //   }catch(err){
  //     console.log(err);
  //   }
  // }

  const postVideo = async () => {
    try {
      const recording = await createRecording();
      if (!recording) return;
      await openCamera(recording.id);
      await startRecording(recording.id);
      await new Promise(resolve => setTimeout(resolve, 600000)); // Record for 3 seconds
      await clickStopButton(recording.id);
    } catch (error) {
      console.log({error});
    }
  };

  const stopAndUpload = async (recording_id) => {
    const recorded = await stopRecording(recording_id);
    const video_formData = new FormData()
    video_formData.append('video_key',video_key)
    video_formData.append('blob',recorded.blob)
    save_video(video_formData);
    // const command = new PutObjectCommand({
    //   Key: video_key,
    //   Body: recorded.blob,
    //   Bucket: bucket,
    // });
    // try {
    //   const response = await client.send(command);
    //   console.log(response);
    // } catch (err) {
    //   console.error(err);
    // }
    await cancelRecording(recording_id);
    // await closeCamera(recording_id);
  };

  const clickStartButton = async () => {
    setLoadingMessage("말씀해주세요.")
    postVideo();
    recorderControls.startRecording();
  };

  const clickStopButton = (recording_id) => {
    const file_name = cookies.get('itv_no') + '-' + count;
    setAudio_key(`audio/${file_name + '.mp3'}`);
    setVideo_key(`video/${file_name + '.webm'}`);
    recorderControls.stopRecording();
    stopAndUpload(recording_id);
  };
  const fetchSTT = async () => {
    console.log(audio_key)
    console.log(cookies.get('itv_no'))
    console.log(count)
    var text_path = ''
    try {
      // const response = await axios.post(`${process.env.STT_POST_API}/stt`, {
      //   itv_no: cookies.get('itv_no'),
      //   file_path: audio_key,
      //   question_no: count,
      // });
      const stt_formData = new FormData();
      stt_formData.append('itv_no',cookies.get('itv_no'));
      stt_formData.append('file_path',audio_key);
      stt_formData.append('question_no',count);
      const response = await post_stt(stt_formData);
      console.log(response);
      console.log('STT 끝');
      setLoadingMessage("다음 질문 생성 중입니다. 잠시 기다려주세요."); // 로딩 메시지 설정
      await setTextPath(response.s3_file_path);
      text_path = response.s3_file_path;

    //질문 끝난 후 db에 post
    const newqs_formData = new FormData();
    newqs_formData.append('user_id',cookies.get('email'));
    newqs_formData.append('itv_no',cookies.get('itv_no'));
    newqs_formData.append('qs_no',count);
    newqs_formData.append('qs_content',frontQ);
    newqs_formData.append('qs_video_url',`s3://simulation-userdata/${video_key}`);
    newqs_formData.append('qs_audio_url',`s3://simulation-userdata/${audio_key}`);
    newqs_formData.append('qs_text_url',text_path);
    post_new_qs(newqs_formData);
    // Count 증가
    setCount(count + 1);
    // axios.post(`${process.env.POST_API}/new_qs`,
    //   {
    //     user_id: cookies.get('email'),
    //     itv_no: cookies.get('itv_no'),
    //     qs_no: count,
    //     qs_content: frontQ,
    //     qs_video_url: `s3://simulation-userdata/${video_key}`,
    //     qs_audio_url: `s3://simulation-userdata/${audio_key}`,
    //     qs_text_url: text_path
    //   })
    // .then(function (response) {
    //   console.log(response);
    //    // Count 증가
    //    setCount(count + 1);
    //    console.log(count);
    // })
    // .catch(function (error) {
    //   console.log(error);
    // });
  } catch (error) {
    console.log(error);
  }

    //Q1 끝난 후 Q1에 대한 사용자 답변 text S3 url 꼬리질문 api에 post

    try{
      // const response2 = await axios.post(`${process.env.CHAT_POST_API}/chat/`,
      //   {
      //     //text_url: response.data.s3_file_path
      //     text_url: text_path,
      //     thread_id: cookies.get('thread_id')
      //   })
        const chat_formData = new FormData();
        chat_formData.append('text_url',text_path);
        chat_formData.append('thread_id',cookies.get('thread_id'));
        const chat_response = await post_chat(chat_formData);
        console.log(chat_response);
        console.log(chat_response.stop)
        // console.log({
        //   text_url: response.data.s3_file_path
        // });
        setchatQ(chat_response.response);
        //router.push('/report');
        if (chat_response.stop === 1) {
          router.push('/report')
        }
        console.log('다음 질문');
        setLoadingMessage("다음 질문으로 넘어가시려면 NEXT 버튼을 눌러주세요"); // 로딩 메시지 설정
      } catch (error) {
        console.log(error);
    }
  };

  const clickNextButton = async() => {
    setLoadingMessage("대답하실 준비가 되면 start버튼을 눌러주세요."); // 로딩 메시지 설정
    await setFrontQ(chatQ);
    polly(chatQ);
    // try{

    //   const response2 = await axios.post('http://192.168.0.4:8888/chat/',
    //     {
    //       //text_url: response.data.s3_file_path
    //       text_url: "s3://simulation-userdata/text/test.txt",
    //       thread_id: cookies.get('thread_id')

    //     })

    //     console.log(response2);
    //     console.log(response2.data.stop)
    //     // console.log({
    //     //   text_url: response.data.s3_file_path
    //     // });


    //     setchatQ(response2.data.response);
    //     if (response2.data.stop === 1) {
    //       router.push('/report')
    //     }

    //     //router.push('/report');

    //   } catch (error) {
    //     console.log(error);

    // }


  }

  useEffect(() => {
  if (start == 0) {
    polly(question);
    setStart(1);
  }
}, [start]);

  return (
    <div className="container mx-auto">
      <div className="my-8">
        <h2 className="text-3xl font-semibold mb-4">면접 질문</h2>
        <div className="bg-gray-100 p-4 mb-8">
          <p className="text-lg">{frontQ}</p>
        </div>
      </div>
      <div className="relative">
        <div className="text-center text-white rounded-lg overflow-hidden shadow-xl aspect-w-16 aspect-h-9 max-w-5xl mx-auto">
          {/* 비디오 재생을 위한 <video> 태그 */}
          <ReactPlayer className="w-full h-auto mx-auto"
          url='https://www.youtube.com/embed/IFmto-5_oK8?si=7uAh7Lb7A8BLjIM0'
          width="960px"
          height="540px"
          muted={true}
          loop={true}
          playing={true}
          volume="0" />
        </div>
        <div style={{display: 'none' }}>
        <AudioRecorder
          onRecordingComplete={addAudioElement}
          audioTrackConstraints={{
            noiseSuppression: true,
            echoCancellation: true,
          }}
          showVisualizer={true}
          recorderControls={recorderControls}
        />
      </div>
        <button onClick={clickStartButton} className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400">
          Start
        </button>
        <button onClick={fetchSTT} className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400">STT</button>

      </div>
      <div className="text-center mt-8">
        {activeRecordings.map(recording => (
          <div key={recording.id}>
            <h2>{recording.status}</h2>
            <video style={{display: 'none' }} ref={recording.webcamRef} autoPlay muted/>
            {/* <video ref={recording.previewRef} autoPlay loop /> */}
            <button onClick={() => clickStopButton(recording.id)} className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400">
              END
            </button>

          </div>
        ))}
        <button onClick={clickNextButton} className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400">
              NEXT
            </button>
            <div>
            {loadingMessage && <label>{loadingMessage}</label>}

            </div>
          

      </div>

    </div>
  );
};

export default Interview;
