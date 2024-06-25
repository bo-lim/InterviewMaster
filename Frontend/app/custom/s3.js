import { PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
const bucket = process.env.BUCKET_NAME;
const s3_client = new S3Client({
    region: 'ap-northeast-2',
    credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    },
});

export const uploadFileToS3 = async (file, user_id) => {
    console.log(bucket);
    const file_key = `coverletter/${user_id}_${Date.now()}_${file.name}`;
    const command = new PutObjectCommand({
      Key: file_key,
      Body: file,
      Bucket: 'simulation-userdata',
    });
  
    try {
      const response = await s3_client.send(command);
      return file_key;
    } catch (err) {
      throw new Error(`Error uploading file: ${err.message}`);
    }
  };
