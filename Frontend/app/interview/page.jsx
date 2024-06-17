'use client';
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useRecordWebcam } from 'react-record-webcam';
import { PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { AudioRecorder,useAudioRecorder } from 'react-audio-voice-recorder';
import { PollyClient,SynthesizeSpeechCommand } from "@aws-sdk/client-polly";
import YouTube, { YouTubeProps } from 'react-youtube';
import ReactPlayer from 'react-player'

const Interview = () => {
  const [start, setStart] = useState(0);
  const router = useRouter();
  //받은 데이터값 출력 test
  // console.log(router.query.data)
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

  const client = new S3Client({
    region: 'ap-northeast-2',
    credentials: {
      accessKeyId: process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY,
    },
  });
  const polly_client = new PollyClient({
    region: 'ap-northeast-2',
    credentials: {
      accessKeyId: process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY,
    },
  });
  const bucket = 'simulation-userdata'
  const file_name = Date.now();
  const audio_key = `audio/${file_name + '.mp3'}`;
  const video_key = `video/${file_name + '.webm'}`;
  const recorderControls = useAudioRecorder();
  const addAudioElement = (blob) => {
    const command = new PutObjectCommand({
      Key: audio_key,
      Body: blob,
      Bucket: bucket,
    });
  
    try {
      const response = client.send(command);
      console.log(response);
    } catch (err) {
      console.error(err);
    }
  };
  const polly = () => {
    const params = {
      "OutputFormat": "mp3",
      "Text": "안녕하세요. 테스트 중입니다.",
      "TextType": "text",
      "VoiceId": "Seoyeon"
    };
    const command = new SynthesizeSpeechCommand(params);
    try{
      polly_client.send(command)
      .then(async (data) => {
        // Convert the ArrayBuffer to a Blob
        console.log(data.AudioStream)
        const arrayBuffer = await data.AudioStream.transformToByteArray();
        console.log(arrayBuffer)
        const blob = new Blob([arrayBuffer], { type: 'audio/mp3' });
        console.log(blob)

        // Create a URL for the Blob and play the audio
        const audioUrl = URL.createObjectURL(blob);
        console.log(audioUrl)
        const audio = new Audio(audioUrl);
        console.log(audio)
        audio.play();
      })
    }catch(err){
      console.log(err);
    }
  }
  

  const postVideo = async () => {
    try {
      const recording = await createRecording();
      if (!recording) return;
      await openCamera(recording.id);
      await startRecording(recording.id);
      await new Promise(resolve => setTimeout(resolve, 6000)); // Record for 3 seconds
      await clickStopButton(recording.id);
    } catch (error) {
      console.log({error});
    }
  };

  const stopAndUpload = async (recording_id) => {
    const recorded = await stopRecording(recording_id);
    const command = new PutObjectCommand({
      Key: video_key,
      Body: recorded.blob,
      Bucket: bucket,
    });
    try {
      const response = await client.send(command);
      console.log(response);
    } catch (err) {
      console.error(err);
    }
    await closeCamera(recording_id);
  };

  const clickStartButton = async () => {
    postVideo();
    recorderControls.startRecording();
  };

  const clickStopButton = async (recording_id) => {
    recorderControls.stopRecording();
    stopAndUpload(recording_id);
  };


   

  // useEffect(() => {
  //   if (router.query.data) {
  //     setInterviewData(JSON.parse(router.query.data));
  //   }
  // }, [router.query.data]);

  return (
    <div className="container mx-auto">
      <div className="my-8">
        <h2 className="text-3xl font-semibold mb-4">면접 질문</h2>
        <div className="bg-gray-100 p-4 mb-8">
          <p className="text-lg">여기에 면접 질문 내용이 들어갑니다.</p>
          <p className="text-lg">예시 질문: 자기소개, 경험, 역량 등</p>
        </div>
      </div>
      <div className="relative">
        <div className="bg-black text-white rounded-lg overflow-hidden shadow-xl aspect-w-16 aspect-h-9 max-w-5xl mx-auto">
          {/* 비디오 재생을 위한 <video> 태그 */}
          <ReactPlayer className="w-full h-auto"
          url='https://www.youtube.com/embed/IFmto-5_oK8?si=7uAh7Lb7A8BLjIM0'
          muted={true}
          loop={true}
          playing={true}
          volume="0" />
        </div>
        <button onClick={() => clickStartButton()} className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400">
          Start
        </button>
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
      </div>
      <div className="text-center mt-8">
        {activeRecordings.map(recording => (
          <div key={recording.id}>
            <h2>{recording.status}</h2>
            <video style={{display: 'none' }} ref={recording.webcamRef} autoPlay muted/>
            {/* <video ref={recording.previewRef} autoPlay loop /> */}
            <button onClick={() => clickStopButton(recording.id)} className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400">
              Next
            </button>
          </div>
        ))}
      </div>
      
    </div>
  );
};

export default Interview;
