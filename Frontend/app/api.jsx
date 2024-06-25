"use server";
import { PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
const bucket = process.env.BUCKET_NAME;
const s3_client = new S3Client({
    region: 'ap-northeast-2',
    credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    },
});
const polly_client = new PollyClient({
  region: 'ap-northeast-2',
  credentials: {
    accessKeyId: process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY,
  },
});


export async function uploadFileToS3(formData){
    const file = formData.get('file');
    const arrayBuffer = await file.arrayBuffer();
    const user_id = formData.get('user_id');
    
    const file_key = `coverletter/${user_id}_${Date.now()}_${file.name}`;
    const command = new PutObjectCommand({
      Key: file_key,
      Body: arrayBuffer,
      Bucket: bucket,
    });
  
    try {
      const response = await s3_client.send(command);
      return `s3://${bucket}/${file_key}`;
    } catch (err) {
      throw new Error(`Error uploading file: ${err.message}`);
    }
};

export async function getUserList(user_id) { // 함수 인자에 user_id 추가
  const response = await fetch(`${process.env.GET_API}/get_user/${user_id}`); // 템플릿 리터럴로 user_id 포함
//   console.log("mypage list", response.json())
  if (!response.ok) throw new Error("Failed to fetch data");
  return response.json();
}

// 자소서 페이지 관심직무, 파일첨부 post
//API_URL2
export async function postItv(formData) {
  const user_id = formData.get("user_id");
  const itv_text_url = formData.get("itv_text_url");
  const itv_cate = formData.get("itv_cate");
  const itv_job = formData.get("itv_job");
//   headers: {"Content-Type": "application/json",},

  try {
    // user_id 전송
    const response = await fetch(`${process.env.POST_API}/new_itv`, {
      method: 'POST',
      headers: {"Content-Type": "application/json",},
      body: JSON.stringify({
        user_id: user_id,
        itv_text_url: itv_text_url,
        itv_cate: itv_cate,
        itv_job: itv_job
      }),
    });

    console.log(response)

    if (!response.ok) {
        const errorDetails = await response.text();
        console.error('Error details:', errorDetails);
        throw new Error("Failed to post new_itv");
    }

    // console.log("post itv: 등록완료");
    return response.json();
  } catch (error) {
    console.error("Error:", error);
    return "itv 정보 등록에 실패했습니다.";
  }
}

export async function postCV(formData) {
  const coverletter_url = formData.get("coverletter_url");
  const position = formData.get("position");
  console.log(formData);

  try {
    // user_id 전송
    const response = await fetch(`${process.env.CHAT_POST_API}/coverletter/`, {
      method: 'POST',
      headers: {"Content-Type": "application/json",},
      body: JSON.stringify({
        coverletter_url: coverletter_url,
        position: position
      }),
    });

    console.log(response)

    if (!response.ok) {
        const errorDetails = await response.text();
        // console.error('Error details:', errorDetails);
        throw new Error("Failed to post new_itv");
    }

    // console.log("post itv: 등록완료");
    return response.json();
  } catch (error) {
    console.error("Error:", error);
    return "itv 정보 등록에 실패했습니다.";
  }
}