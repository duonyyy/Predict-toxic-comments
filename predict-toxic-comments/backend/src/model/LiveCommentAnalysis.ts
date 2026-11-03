import mongoose, { Document, Schema } from 'mongoose'

export interface ILiveCommentAnalysis extends Document {
    comment_id: string
    video_id: string
    author_id: string
    author_name: string
    author_image: string
    message: string
    cleaned_message?: string
    published_at: Date
    toxicity: 'TOXIC' | 'NON-TOXIC'
    expression_type?: 'EXPLICIT' | 'IMPLICIT' | null
    toxic_label: string
    toxic_category: string
    toxic_score: number
    implicit_score?: number
    recommended_action: 'Ban' | 'Hide' | 'Pending' | 'Safe'
    predictions?: {
        toxic?: number
        non_toxic?: number
        explicit?: number
        implicit?: number
    }
}

const LiveCommentAnalysisSchema: Schema = new Schema({
    comment_id: { type: String, required: true, unique: true },
    video_id: { type: String, required: true, index: true },
    author_id: { type: String, required: true },
    author_name: { type: String, required: true },
    author_image: { type: String },
    message: { type: String, required: true },
    cleaned_message: { type: String },
    published_at: { type: Date, required: true },
    toxicity: { type: String, enum: ['TOXIC', 'NON-TOXIC'], default: 'NON-TOXIC' },
    expression_type: { type: String, enum: ['EXPLICIT', 'IMPLICIT', null], default: null },
    toxic_label: { type: String, required: true },
    toxic_category: { type: String, required: true },
    toxic_score: { type: Number, default: 0 },
    implicit_score: { type: Number, default: 0 },
    recommended_action: { type: String, enum: ['Ban', 'Hide', 'Pending', 'Safe'], required: true },
    predictions: { type: Schema.Types.Mixed },
}, {
    timestamps: true
})

export const CommentModel = mongoose.model<ILiveCommentAnalysis>('LiveCommentAnalysis', LiveCommentAnalysisSchema, "live_comment_analysis")
