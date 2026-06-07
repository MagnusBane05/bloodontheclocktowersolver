import { CloseButton } from "../CloseButton";

export function ModalHeader({content, onClose}: {content: string, onClose?: () => void}) {
    return (
        <div className='flex flex-row justify-between items-start'>
            <h2 className="text-lg font-semibold text-white mb-4">
                {content}
            </h2>
            {onClose != null && <CloseButton onClose={onClose} />}
        </div>
    );
}